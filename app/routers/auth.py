
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AuthenticationEvent, SecurityNotification
from app.models.user import User
from app.models.idp_login_marker import IdPLoginMarker
from app.schemas.authentication_activity import AuthenticationActivityView
from app.schemas.security_notification import SecurityNotificationView
from app.schemas.user import Token, UserCreate, UserLogin, UserRead
from app.services.security_notification_service import (
    create_authentication_notification,
)
from app.services.idp_session_service import (
    create_idp_session,
    revoke_idp_session,
)
from app.services.user_service import (
    authenticate_user,
    create_user,
    get_user_by_matric,
)
from app.utils.jwt import create_access_token, get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Register a new user.

    The first user is created as an administrator.
    Public registration is disabled afterward unless explicitly enabled.
    """
    existing_count = db.query(User).count()

    if existing_count == 0:
        return create_user(
            db,
            email=payload.email,
            password=payload.password,
            matric_no=payload.matric_no,
            full_name=payload.full_name,
            role="admin",
        )

    if settings.allow_public_registration:
        try:
            return create_user(
                db,
                email=payload.email,
                password=payload.password,
                matric_no=payload.matric_no,
                full_name=payload.full_name,
                role=payload.role,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Public registration is disabled. "
            "Contact ABU ICT for account creation."
        ),
    )


@router.post("/login", response_model=Token)
def login(
    payload: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate a user and audit the password login attempt."""

    user = authenticate_user(
        db,
        payload.matric_no,
        payload.password,
    )

    ip_address = (
        request.client.host
        if request.client
        else None
    )
    user_agent = request.headers.get("user-agent")

    if not user:
        known_user = get_user_by_matric(
            db,
            payload.matric_no,
        )

        db.add(
            AuthenticationEvent(
                user_id=known_user.id if known_user else None,
                client_id=None,
                application_name="ABU-SSO Portal",
                event_type="login",
                outcome="failure",
                authentication_method="password",
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason="invalid_credentials",
            )
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid matric/staff number or password",
        )

    token = create_access_token(user.id)

    session_record, session_token = create_idp_session(
        db=db,
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    login_marker = IdPLoginMarker(
        session_id=session_record.id,
    )

    try:
        db.add(login_marker)

        login_event = AuthenticationEvent(
            user_id=user.id,
            client_id=None,
            application_name="ABU-SSO Portal",
            event_type="login",
            outcome="success",
            authentication_method="password",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(login_event)
        db.flush()
        create_authentication_notification(db, login_event)

        db.commit()

    except Exception:
        db.rollback()
        raise

    response.set_cookie(
        key="abu_idp_session",
        value=session_token,
        max_age=settings.oidc_idp_session_expire_hours * 60 * 60,
        httponly=True,
        secure=settings.oidc_issuer.startswith("https://"),
        samesite="lax",
        path="/",
    )

    return Token(access_token=token)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Revoke the central IdP session and clear its browser cookie."""

    session_token = request.cookies.get("abu_idp_session")

    revoked = revoke_idp_session(db, session_token)

    response.delete_cookie(
        key="abu_idp_session",
        path="/",
        httponly=True,
        secure=settings.oidc_issuer.startswith("https://"),
        samesite="lax",
    )

    return {
        "message": (
            "Central IdP session revoked."
            if revoked
            else "No active central IdP session found."
        )
    }


@router.get("/me", response_model=UserRead)
def me(current_user=Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@router.get(
    "/activity",
    response_model=list[AuthenticationActivityView],
)
def get_authentication_activity(
    limit: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the latest central login and one latest access per campus service."""

    latest_idp_login = (
        db.query(AuthenticationEvent)
        .filter(
            AuthenticationEvent.user_id == current_user.id,
            AuthenticationEvent.application_name == "ABU-SSO Portal",
            AuthenticationEvent.event_type == "login",
            AuthenticationEvent.outcome == "success",
        )
        .order_by(AuthenticationEvent.occurred_at.desc())
        .first()
    )

    service_accesses = (
        db.query(AuthenticationEvent)
        .filter(
            AuthenticationEvent.user_id == current_user.id,
            AuthenticationEvent.application_name != "ABU-SSO Portal",
            AuthenticationEvent.event_type == "authorization",
            AuthenticationEvent.outcome == "success",
        )
        .order_by(AuthenticationEvent.occurred_at.desc())
        .all()
    )

    latest_by_service = {}
    for event in service_accesses:
        if event.application_name not in latest_by_service:
            latest_by_service[event.application_name] = event

    activities = list(latest_by_service.values())
    if latest_idp_login is not None:
        activities.append(latest_idp_login)

    activities.sort(
        key=lambda event: event.occurred_at,
        reverse=True,
    )
    return activities[:limit]


@router.get(
    "/notifications",
    response_model=list[SecurityNotificationView],
)
def get_security_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return security notifications belonging only to the current user."""

    return (
        db.query(SecurityNotification)
        .filter(
            SecurityNotification.user_id == current_user.id
        )
        .order_by(SecurityNotification.created_at.desc())
        .limit(limit)
        .all()
    )


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=SecurityNotificationView,
)
def mark_security_notification_as_read(
    notification_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark one of the current user's notifications as read."""

    notification = (
        db.query(SecurityNotification)
        .filter(
            SecurityNotification.id == notification_id,
            SecurityNotification.user_id == current_user.id,
        )
        .first()
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)

    return notification
