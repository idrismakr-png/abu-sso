
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OIDCClient
from app.schemas.admin import (
    AdminRoleUpdateRequest,
    AdminStats,
    AdminTopUpRequest,
    UserAdminView,
)
from app.schemas.application_registry import (
    ApplicationRegistrationRequest,
    ApplicationRegistryView,
)
from app.schemas.user import UserCreate
from app.schemas.wallet import TransactionRead
from app.services import admin_service
from app.services.application_registry_service import create_application
from app.services.user_service import create_user
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


@router.post(
    "/users",
    response_model=UserAdminView,
    status_code=status.HTTP_201_CREATED,
)
def create_new_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    """Create a new user account (admin only)."""
    try:
        return create_user(
            db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
            matric_no=payload.matric_no,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/wallet/topup",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
)
def top_up_other_wallet(
    payload: AdminTopUpRequest,
    db: Session = Depends(get_db),
):
    """Credit another user's wallet (admin only)."""
    try:
        return admin_service.admin_top_up(
            db,
            payload.user_id,
            payload.amount,
            payload.description,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/stats", response_model=AdminStats)
def stats(db: Session = Depends(get_db)):
    """Aggregate statistics for the admin dashboard."""
    return admin_service.get_stats(db)


@router.post(
    "/applications",
    status_code=status.HTTP_201_CREATED,
)
def register_application(
    payload: ApplicationRegistrationRequest,
    db: Session = Depends(get_db),
):
    """
    Register an approved application with ABU-SSO.

    A confidential client secret is returned only once, during registration.
    """
    try:
        application, client_secret = create_application(
            db,
            name=payload.name,
            client_type=payload.client_type,
            redirect_uris=payload.redirect_uris,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    result = ApplicationRegistryView.model_validate(
        application
    ).model_dump()

    if client_secret is not None:
        result["client_secret"] = client_secret

    return result


@router.get(
    "/applications",
    response_model=list[ApplicationRegistryView],
)
def list_applications(db: Session = Depends(get_db)):
    """List all applications registered with ABU-SSO."""
    return (
        db.query(OIDCClient)
        .order_by(OIDCClient.created_at.desc())
        .all()
    )


@router.patch("/applications/{client_id}/active")
def change_application_status(
    client_id: str,
    active: bool,
    db: Session = Depends(get_db),
):
    """Activate or deactivate a registered application."""
    application = (
        db.query(OIDCClient)
        .filter_by(client_id=client_id)
        .first()
    )

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    application.is_active = active

    try:
        db.commit()
        db.refresh(application)
    except Exception:
        db.rollback()
        raise

    return ApplicationRegistryView.model_validate(
        application
    )
