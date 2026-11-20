
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import OIDCClient, User
from app.models.oidc_token import OIDCAccessToken


def utcnow():
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def _as_utc(value):
    """Convert a database timestamp to a timezone-aware UTC timestamp."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def generate_access_token(
    grant_type,
    client,
    user=None,
    scope=None,
    expires_in=None,
    include_refresh_token=False,
):
    """Generate an opaque bearer access token for an authorised OIDC client."""

    if grant_type != "authorization_code":
        raise ValueError("Unsupported OIDC token grant type")

    if include_refresh_token:
        raise ValueError("Refresh tokens are not yet supported")

    lifetime = (
        expires_in
        if expires_in is not None
        else settings.oidc_access_token_expire_minutes * 60
    )

    if (
        not isinstance(lifetime, int)
        or isinstance(lifetime, bool)
        or lifetime <= 0
    ):
        raise ValueError("Access token lifetime must be a positive integer")

    token = {
        "token_type": "Bearer",
        "access_token": secrets.token_urlsafe(32),
        "expires_in": lifetime,
    }

    if scope:
        token["scope"] = scope

    return token


def persist_access_token(
    db,
    token,
    client_id,
    user_id,
    commit=True,
):
    """Persist an access token hash, optionally within an existing transaction."""

    raw_token = token.get("access_token")
    lifetime = token.get("expires_in")

    if not isinstance(raw_token, str) or not raw_token:
        raise ValueError("A valid access token is required")

    if (
        not isinstance(lifetime, int)
        or isinstance(lifetime, bool)
        or lifetime <= 0
    ):
        raise ValueError("Access token lifetime must be a positive integer")

    if not client_id or not user_id:
        raise ValueError("Client ID and user ID are required")

    scope = token.get("scope", "")

    if isinstance(scope, str):
        scopes = scope.split()
    elif isinstance(scope, list):
        scopes = scope
    else:
        raise ValueError("Access token scopes must be a string or list")

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    record = OIDCAccessToken(
        token_hash=token_hash,
        client_id=client_id,
        user_id=user_id,
        scopes=scopes,
        expires_at=utcnow() + timedelta(seconds=lifetime),
    )

    try:
        db.add(record)
        db.flush()

        if commit:
            db.commit()
            db.refresh(record)

    except Exception:
        db.rollback()
        raise

    return record


def get_userinfo_for_access_token(
    db: Session,
    raw_token: str,
):
    """
    Validate an opaque access token and return its permitted OIDC user claims.

    Invalid, expired, revoked, or inactive credentials return None.
    """

    if not isinstance(raw_token, str) or not raw_token:
        return None

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    token_record = (
        db.query(OIDCAccessToken)
        .filter_by(
            token_hash=token_hash,
            revoked_at=None,
        )
        .first()
    )

    if token_record is None:
        return None

    if _as_utc(token_record.expires_at) <= utcnow():
        return None

    client = (
        db.query(OIDCClient)
        .filter_by(
            client_id=token_record.client_id,
            is_active=True,
        )
        .first()
    )

    if client is None:
        return None

    user = (
        db.query(User)
        .filter_by(
            id=token_record.user_id,
            is_active=True,
        )
        .first()
    )

    if user is None:
        return None

    scopes = set(token_record.scopes or [])

    if "openid" not in scopes:
        return None

    claims = {
        "sub": user.id,
    }

    if "profile" in scopes and user.full_name:
        claims["name"] = user.full_name

    if "email" in scopes:
        claims["email"] = user.email

    return claims
