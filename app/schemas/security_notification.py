
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SecurityNotificationView(BaseModel):
    """Safe notification details visible only to the account owner."""

    id: str
    title: str
    message: str
    created_at: datetime
    read_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
