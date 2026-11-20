import secrets

from app.config import settings


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

    if not isinstance(lifetime, int) or lifetime <= 0:
        raise ValueError("Access token lifetime must be a positive integer")

    token = {
        "token_type": "Bearer",
        "access_token": secrets.token_urlsafe(32),
        "expires_in": lifetime,
    }

    if scope:
        token["scope"] = scope

    return token