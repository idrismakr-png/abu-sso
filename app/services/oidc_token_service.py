
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.models.oidc_token import OIDCAccessToken


def utcnow():
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


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


def persist_access_token(db, token, client_id, user_id):
    """Persist an access token's hash without storing its raw value."""

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
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise

    return record
