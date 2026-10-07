from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.wallet import Transaction, Wallet
from app.services.wallet_service import get_or_create_wallet, top_up


def list_all_users(db: Session, limit: int = 200) -> list[User]:
    """Return all users, newest first."""
    return (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(limit)
        .all()
    )


def set_user_role(db: Session, user_id: str, new_role: str) -> User:
    """Change a user's role. Raises ValueError if user not found."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User not found: {user_id}")
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


def set_user_active(db: Session, user_id: str, active: bool) -> User:
    """Activate or deactivate a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User not found: {user_id}")
    user.is_active = active
    db.commit()
    db.refresh(user)
    return user


def admin_top_up(
    db: Session,
    user_id: str,
    amount: Decimal,
    description: Optional[str] = None,
) -> Transaction:
    """Credit another user's wallet as an administrator."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User not found: {user_id}")
    wallet = get_or_create_wallet(db, user)
    return top_up(
        db,
        wallet,
        amount,
        description or f"Admin top-up by administrator",
    )


def get_stats(db: Session) -> dict:
    """Aggregate metrics for the admin dashboard."""
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = (
        db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    )
    total_wallets = db.query(func.count(Wallet.id)).scalar() or 0
    total_balance = db.query(func.coalesce(func.sum(Wallet.balance), 0)).scalar() or Decimal("0.00")
    total_transactions = db.query(func.count(Transaction.id)).scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_wallets": total_wallets,
        "total_balance": Decimal(str(total_balance)),
        "total_transactions": total_transactions,
    }