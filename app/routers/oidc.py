
from urllib.parse import parse_qs, urlencode, urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AuthenticationEvent
from app.services.idp_session_service import get_active_idp_session
from app.services.oidc_server import create_authorization_server
from app.services.oidc_token_service import (
    get_userinfo_for_access_token,
)
from app.utils.oidc_keys import get_jwks
from app.utils.oidc_requests import create_oauth2_request


router = APIRouter()


@router.get("/.well-known/openid-configuration", tags=["OIDC"])
def openid_configuration():
    issuer = settings.oidc_issuer.rstrip("/")

    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/authorize",
        "token_endpoint": f"{issuer}/token",
        "userinfo_endpoint": f"{issuer}/userinfo",
        "jwks_uri": f"{issuer}/jwks.json",
        "response_types_supported": ["code"],
        "response_modes_supported": ["query"],
        "grant_types_supported": ["authorization_code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": [
            settings.oidc_signing_algorithm
        ],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": [
            "none",
            "client_secret_basic",
            "client_secret_post",
        ],
        "code_challenge_methods_supported": ["S256"],
        "claims_supported": [
            "sub",
            "name",
            "email",
            "iss",
            "aud",
            "exp",
            "iat",
            "auth_time",
            "nonce",
        ],
    }


@router.get("/authorize", tags=["OIDC"])
async def authorize(
    request: Request,
    db: Session = Depends(get_db),
):
    oauth_request = await create_oauth2_request(request, db=db)

    session_token = request.cookies.get("abu_idp_session")
    prompt_values = request.query_params.get("prompt", "").split()
    force_login = "login" in prompt_values

    session_result = (
        None
        if force_login
        else get_active_idp_session(db, session_token)
    )

    if session_result is None:
        next_url = request.url.path

        if request.url.query:
            next_url = f"{next_url}?{request.url.query}"

        return RedirectResponse(
            url="/login?" + urlencode({"next": next_url}),
            status_code=303,
        )

    session_record, user = session_result

    oauth_request.user = user

    server = create_authorization_server(db)

    response = server.create_authorization_response(
        request=oauth_request,
        grant_user=user,
    )

    location = response.headers.get("location")

    if response.status_code in (302, 303) and location:
        response_parameters = parse_qs(
            urlsplit(location).query
        )

        if "code" in response_parameters:
            client = getattr(oauth_request, "client", None)

            if client is not None:
                db.add(
                    AuthenticationEvent(
                        user_id=user.id,
                        client_id=client.client_id,
                        application_name=client.name,
                        event_type="authorization",
                        outcome="success",
                        authentication_method="existing_sso_session",
                        ip_address=(
                            request.client.host
                            if request.client
                            else None
                        ),
                        user_agent=request.headers.get("user-agent"),
                    )
                )
                db.commit()

    return response


@router.post("/token", tags=["OIDC"])
async def token(
    request: Request,
    db: Session = Depends(get_db),
):
    oauth_request = await create_oauth2_request(
        request,
        db=db,
    )

    server = create_authorization_server(db)

    return server.create_token_response(
        request=oauth_request,
    )


@router.get("/userinfo", tags=["OIDC"])
def userinfo(
    request: Request,
    db: Session = Depends(get_db),
):
    authorization = request.headers.get("Authorization", "")
    parts = authorization.split()

    if (
        len(parts) != 2
        or parts[0].lower() != "bearer"
        or not parts[1]
    ):
        raise HTTPException(
            status_code=401,
            detail="A valid bearer access token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = get_userinfo_for_access_token(
        db=db,
        raw_token=parts[1],
    )

    if claims is None:
        raise HTTPException(
            status_code=401,
            detail="The access token is invalid, expired, or revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return claims


@router.get("/jwks.json", tags=["OIDC"])
def jwks():
    return get_jwks()
