from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def health_check():
    """Simple liveness probe for the ABU-SSO API."""
    return {"status": "healthy", "service": "abu-sso"}
