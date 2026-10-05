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
    """Look up a user by matric number."""
    return db.query(User).filter(User.matric_no == matric_no).first()


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    role: str = "student",
    matric_no: Optional[str] = None,
) -> User:
    """Create a new user. Raises ValueError if the email is already taken."""
    email = email.lower().strip()
    if get_user_by_email(db, email):
        raise ValueError(f"Email already registered: {email}")

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        matric_no=matric_no,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Return the user if credentials are valid, otherwise None."""
    user = get_user_by_email(db, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user