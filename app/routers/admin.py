from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.admin import (
    AdminRoleUpdateRequest,
    AdminStats,
    AdminTopUpRequest,
    UserAdminView,
)
from app.schemas.wallet import TransactionRead
from app.services import admin_service
from app.utils.rbac import require_role

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role("admin"))],
)


@router.get("/users", response_model=list[UserAdminView])
def list_users(db: Session = Depends(get_db)):
    """List all registered users (admin only)."""
    return admin_service.list_all_users(db)


@router.patch("/users/{user_id}/role", response_model=UserAdminView)
def change_role(
    user_id: str,
    payload: AdminRoleUpdateRequest,
    db: Session = Depends(get_db),
):
    """Change a user's role (admin only)."""
    try:
        return admin_service.set_user_role(db, user_id, payload.role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/users/{user_id}/active", response_model=UserAdminView)
def change_active(
    user_id: str,
    active: bool,
    db: Session = Depends(get_db),
):
    """Activate or deactivate a user account (admin only)."""
    try:
        return admin_service.set_user_active(db, user_id, active)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/wallet/topup", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def top_up_other_wallet(
    payload: AdminTopUpRequest,
    db: Session = Depends(get_db),
):
    """Credit another user's wallet (admin only)."""
    try:
        return admin_service.admin_top_up(
            db, payload.user_id, payload.amount, payload.description
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/stats", response_model=AdminStats)
def stats(db: Session = Depends(get_db)):
    """Aggregate statistics for the admin dashboard."""
    return admin_service.get_stats(db)
    