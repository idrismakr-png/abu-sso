import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    balance = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    transactions = relationship(
        "Transaction",
        back_populates="wallet",
        cascade="all, delete-orphan",
        order_by="desc(Transaction.created_at)",
    )

    def __repr__(self) -> str:
        return f"<Wallet user_id={self.user_id} balance={self.balance}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wallet_id = Column(String(36), ForeignKey("wallets.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    type = Column(String(20), nullable=False)  # credit | debit
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    wallet = relationship("Wallet", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.type} {self.amount}>"
        