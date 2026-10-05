from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.wallet import Transaction, Wallet


def get_or_create_wallet(db: Session, user: User) -> Wallet:
    """Return the user's wallet, creating it with 0 balance if it doesn't exist."""
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    if wallet is None:
        wallet = Wallet(user_id=user.id, balance=Decimal("0.00"))
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet


def top_up(db: Session, wallet: Wallet, amount: Decimal, description: Optional[str] = None) -> Transaction:
    """Add funds to a wallet and record a credit transaction."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    wallet.balance = wallet.balance + amount
    txn = Transaction(
        wallet_id=wallet.id,
        amount=amount,
        type="credit",
        description=description or "Wallet top-up",
    )
    db.add(txn)
    db.commit()
    db.refresh(wallet)
    db.refresh(txn)
    return txn


def pay(db: Session, wallet: Wallet, amount: Decimal, description: Optional[str] = None) -> Transaction:
    """Deduct funds from a wallet and record a debit transaction. Raises if insufficient funds."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    if wallet.balance < amount:
        raise ValueError(f"Insufficient funds: balance is {wallet.balance}, requested {amount}")
    wallet.balance = wallet.balance - amount
    txn = Transaction(
        wallet_id=wallet.id,
        amount=amount,
        type="debit",
        description=description or "Payment",
    )
    db.add(txn)
    db.commit()
    db.refresh(wallet)
    db.refresh(txn)
    return txn


def list_transactions(db: Session, wallet: Wallet, limit: int = 50) -> list[Transaction]:
    """Return the most recent transactions for a wallet."""
    return (
        db.query(Transaction)
        .filter(Transaction.wallet_id == wallet.id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )