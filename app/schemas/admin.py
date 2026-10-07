from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserAdminView(BaseModel):
    """User record as seen by an admin (no password hash)."""

    id: str
    email: EmailStr
    full_name: Optional[str]
    role: str
    matric_no: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WalletAdminView(BaseModel):
    """Wallet record for admin listing."""

    user_id: str
    balance: Decimal

    model_config = {"from_attributes": True}


class AdminTopUpRequest(BaseModel):
    """Admin action — credit another user's wallet."""

    user_id: str
    amount: Decimal = Field(gt=0, le=1_000_000)
    description: Optional[str] = Field(default=None, max_length=255)


class AdminRoleUpdateRequest(BaseModel):
    """Admin action — change a user's role."""

    role: str = Field(pattern="^(student|staff|admin)$")


class AdminStats(BaseModel):
    """Dashboard summary metrics for the admin page."""

    total_users: int
    active_users: int
    total_wallets: int
    total_balance: Decimal
    total_transactions: int