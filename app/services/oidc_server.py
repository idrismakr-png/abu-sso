
import hashlib
import time
from datetime import timedelta

from authlib.oauth2.rfc6749 import (
    AuthorizationServer,
    InvalidGrantError,
    InvalidRequestError,
    InvalidScopeError,
    JsonRequest,
)
from authlib.oauth2.rfc6749.grants import AuthorizationCodeGrant
from authlib.oauth2.rfc7636 import CodeChallenge
from authlib.oidc.core.grants import OpenIDCode
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from fastapi.responses import JSONResponse, Response
from sqlalchemy import update

from app.config import settings
from app.models import OIDCClient, OIDCAuthorizationCode, User
from app.models.oidc import utcnow
from app.services.oidc_token_service import (
    generate_access_token,
    persist_access_token,
)
from app.utils.oidc_keys import get_private_key
from app.utils.oidc_requests import ABUOAuth2Request


class ABUCodeChallenge(CodeChallenge):
    """Require PKCE S256 for every authorization request."""

    def validate_code_challenge(self, grant, redirect_uri):
        request = grant.request
        challenge = request.payload.data.get("code_challenge")
        method = request.payload.data.get("code_challenge_method")

        if not challenge:
            raise InvalidRequestError(
                "PKCE code_challenge is required."
            )

        if method != "S256":
            raise InvalidRequestError(
                "Only the S256 PKCE method is supported."
            )

        super().validate_code_challenge(grant, redirect_uri)


class ABUOpenIDCode(OpenIDCode):
    """Configure OpenID Connect ID-token generation."""

    def __init__(self):
        super().__init__(require_nonce=True)

    def resolve_client_private_key(self, client):
        private_key = get_private_key()

        return private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption(),
        )

    def get_client_algorithm(self, client):
        return settings.oidc_signing_algorithm

    def get_encode_header(self, client):
        return {
            "alg": settings.oidc_signing_algorithm,
            "kid": settings.oidc_key_id,
        }

    def get_client_claims(self, client):
        return {
            "iss": settings.oidc_issuer,
            "aud": [client.get_client_id()],
            "exp": (
                int(time.time())
                + settings.oidc_id_token_expire_minutes * 60
            ),
        }

    def exists_nonce(self, nonce, request):
        if not nonce:
            return False

        db = self.grant_database(request)

        existing = (
            db.query(OIDCAuthorizationCode)
            .filter_by(
                client_id=request.payload.client_id,
                nonce=nonce,
            )
            .first()
        )

        return existing is not None

    @staticmethod
    def grant_database(request):
        db = getattr(request, "database_session", None)

        if db is None:
            raise RuntimeError(
                "Database session is missing from the OIDC request."
            )

        return db

    def generate_user_info(self, user, scope):
        claims = {"sub": user.id}

        allowed_scopes = (
            set(scope.split())
            if isinstance(scope, str)
            else set(scope)
        )

        if "profile" in allowed_scopes and user.full_name:
            claims["name"] = user.full_name

        if "email" in allowed_scopes:
            claims["email"] = user.email

        return claims


class ABUAuthorizationCodeGrant(AuthorizationCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = [
        "none",
        "client_secret_basic",
        "client_secret_post",
    ]

    def validate_authorization_request(self):
        redirect_uri = super().validate_authorization_request()

        if "openid" not in self.request.scope.split():
            raise InvalidScopeError(
                "The openid scope is required."
            )

        return redirect_uri

    def save_authorization_code(self, code, request):
        db = request.database_session
        client = request.client

        raw_challenge = request.payload.data.get(
            "code_challenge"
        )
        challenge_method = request.payload.data.get(
            "code_challenge_method"
        )

        if not raw_challenge or challenge_method != "S256":
            raise InvalidRequestError(
                "A valid S256 PKCE challenge is required."
            )

        code_hash = hashlib.sha256(
            code.encode("utf-8")
        ).hexdigest()

        record = OIDCAuthorizationCode(
            code_hash=code_hash,
            client_id=client.client_id,
            user_id=request.user.id,
            redirect_uri=request.payload.redirect_uri,
            scopes=request.scope.split(),
            nonce=request.payload.data.get("nonce"),
            code_challenge=raw_challenge,
            code_challenge_method=challenge_method,
            expires_at=(
                utcnow()
                + timedelta(
                    minutes=settings.oidc_authorization_code_expire_minutes
                )
            ),
        )

        try:
            db.add(record)
            db.commit()
        except Exception:
            db.rollback()
            raise

    def query_authorization_code(self, code, client):
        db = self.request.database_session

        code_hash = hashlib.sha256(
            code.encode("utf-8")
        ).hexdigest()

        return (
            db.query(OIDCAuthorizationCode)
            .filter_by(
                code_hash=code_hash,
                client_id=client.client_id,
                consumed_at=None,
            )
            .filter(
                OIDCAuthorizationCode.expires_at > utcnow()
            )
            .first()
        )

    def delete_authorization_code(self, authorization_code):
        db = self.request.database_session
        consumed_time = utcnow()

        result = db.execute(
            update(OIDCAuthorizationCode)
            .where(
                OIDCAuthorizationCode.id == authorization_code.id,
                OIDCAuthorizationCode.consumed_at.is_(None),
                OIDCAuthorizationCode.expires_at > consumed_time,
            )
            .values(consumed_at=consumed_time)
            .execution_options(synchronize_session=False)
        )

        if result.rowcount != 1:
            raise InvalidGrantError(
                "Authorization code is expired or has already been used."
            )

        db.flush()

    def authenticate_user(self, authorization_code):
        db = self.request.database_session

        return (
            db.query(User)
            .filter_by(
                id=authorization_code.user_id,
                is_active=True,
            )
            .first()
        )

    def create_token_response(self):
        db = self.request.database_session

        try:
            response = super().create_token_response()
            db.commit()
            return response
        except Exception:
            db.rollback()
            raise


class ABUAuthorizationServer(AuthorizationServer):
    def __init__(self, db):
        super().__init__(
            scopes_supported=["openid", "profile", "email"]
        )
        self.db = db

    def query_client(self, client_id):
        return (
            self.db.query(OIDCClient)
            .filter_by(
                client_id=client_id,
                is_active=True,
            )
            .first()
        )

    def save_token(self, token, request):
        persist_access_token(
            db=self.db,
            token=token,
            client_id=request.client.client_id,
            user_id=request.user.id,
            commit=False,
        )

    def create_oauth2_request(self, request):
        if isinstance(request, ABUOAuth2Request):
            return request

        raise TypeError(
            "Convert the Starlette request using create_oauth2_request "
            "before calling the authorization server."
        )

    def create_json_request(self, request):
        if isinstance(request, JsonRequest):
            return request

        raise TypeError(
            "A prepared Authlib JsonRequest is required."
        )

    def handle_response(self, status, body, headers):
        response_headers = dict(headers or [])

        if isinstance(body, dict):
            return JSONResponse(
                content=body,
                status_code=status,
                headers=response_headers,
            )

        return Response(
            content=body,
            status_code=status,
            headers=response_headers,
        )

    def send_signal(self, name, *args, **kwargs):
        return None


def create_authorization_server(db):
    server = ABUAuthorizationServer(db)

    server.register_token_generator(
        "authorization_code",
        generate_access_token,
    )

    server.register_grant(
        ABUAuthorizationCodeGrant,
        extensions=[
            ABUCodeChallenge(required=True),
            ABUOpenIDCode(),
        ],
    )

    return server
