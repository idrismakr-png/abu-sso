from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserRead
from app.services.user_service import authenticate_user, create_user
from app.utils.jwt import create_access_token, get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Register a new user.

    Bootstrap pattern:
    - If the database is EMPTY, the first user is created as an admin.
      This lets a fresh deployment be set up without an existing admin.
    - Otherwise, public registration is DISABLED (403) unless the
      `ALLOW_PUBLIC_REGISTRATION` setting is true (used in tests).
      Real users must be created by an admin via POST /admin/users.
    """
    existing_count = db.query(User).count()

    if existing_count == 0:
        # Bootstrap: first user is always an admin.
        user = create_user(
            db,
            email=payload.email,
            password=payload.password,
            matric_no=payload.matric_no,
            full_name=payload.full_name,
            role="admin",
        )
        return user

    if settings.allow_public_registration:
        # Test / development mode: public registration allowed.
        try:
            user = create_user(
                db,
                email=payload.email,
                password=payload.password,
                matric_no=payload.matric_no,
                full_name=payload.full_name,
                role=payload.role,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        return user

    # Production: public registration closed after bootstrap.
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public registration is disabled. Contact ABU ICT for account creation.",
    )


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with matric/staff number + password and receive a JWT."""
    user = authenticate_user(db, payload.matric_no, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid matric/staff number or password",
        )
    token = create_access_token(user.id)
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
def me(current_user=Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user