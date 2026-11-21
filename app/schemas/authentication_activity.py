
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AuthenticationActivityView(BaseModel):
    """Safe authentication activity details visible to the account owner."""

    id: str
    application_name: str | None
    event_type: str
    outcome: Literal["success", "failure"]
    authentication_method: str | None
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)
