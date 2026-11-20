from fastapi import APIRouter

from app.utils.oidc_keys import get_jwks


router = APIRouter()


@router.get("/jwks.json", tags=["OIDC"])
def jwks():
    """Publish ABU-SSO's public signing keys for OIDC clients."""
    return get_jwks()