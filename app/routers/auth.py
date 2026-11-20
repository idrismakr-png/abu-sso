
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserRead
from app.services.idp_session_service import (
    create_idp_session,
    revoke_idp_session,
)
from app.services.user_service import authenticate_user, create_user
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
    """Authenticate a user and establish JWT and central IdP sessions."""

    user = authenticate_user(
        db,
        payload.matric_no,
        payload.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid matric/staff number or password",
        )

    token = create_access_token(user.id)

    _, session_token = create_idp_session(
        db=db,
        user=user,
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
        user_agent=request.headers.get("user-agent"),
    )

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
