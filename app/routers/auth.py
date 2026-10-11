from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import Token, UserCreate, UserLogin, UserRead
from app.services.user_service import authenticate_user, create_user
from app.utils.jwt import create_access_token, get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account.

    NOTE: in production this endpoint is disabled for the public —
    accounts are created by an administrator via POST /admin/users.
    It remains open here so the API can be bootstrapped and tested.
    """
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