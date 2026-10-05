from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class WalletRead(BaseModel):
    id: str
    user_id: str
    balance: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionRead(BaseModel):
    id: str
    amount: Decimal
    type: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TopUpRequest(BaseModel):
    amount: Decimal = Field(gt=0, le=100000, description="Amount to add (must be positive)")
    description: str | None = Field(default=None, max_length=255)


class PayRequest(BaseModel):
    amount: Decimal = Field(gt=0, le=100000, description="Amount to charge (must be positive)")
    description: str | None = Field(default=None, max_length=255)