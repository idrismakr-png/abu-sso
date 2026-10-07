from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.utils.jwt import get_current_user


def require_role(*allowed_roles: str):
    """FastAPI dependency factory.

    Returns a dependency that resolves the current user and
    raises 403 Forbidden if the user's role is not in `allowed_roles`.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
        def admin_endpoint(): ...
    """
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {' or '.join(allowed_roles)}",
            )
        return current_user

    return _checker
    