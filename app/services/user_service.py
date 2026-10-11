from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.security import hash_password, verify_password


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Look up a user by email (case-insensitive)."""
    return db.query(User).filter(User.email == email.lower()).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Look up a user by primary key."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_matric(db: Session, matric_no: str) -> Optional[User]:
    """Look up a user by matric / staff number (case-insensitive)."""
    return db.query(User).filter(User.matric_no == matric_no.strip().upper()).first()


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    matric_no: str,
    full_name: Optional[str] = None,
    role: str = "student",
) -> User:
    """Create a new user. Raises ValueError on duplicate email or matric."""
    email = email.lower().strip()
    matric = matric_no.strip().upper()

    if get_user_by_email(db, email):
        raise ValueError(f"Email already registered: {email}")
    if get_user_by_matric(db, matric):
        raise ValueError(f"Matric / staff number already registered: {matric}")

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        matric_no=matric,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, matric_no: str, password: str) -> Optional[User]:
    """Return the user if matric/staff number + password are valid, otherwise None."""
    user = get_user_by_matric(db, matric_no)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user