from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Fields required to register a new user."""

    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: str = Field(default="student")
    matric_no: Optional[str] = Field(default=None, max_length=50)


class UserRead(BaseModel):
    """User data returned by the API (never includes password)."""

    id: str
    email: EmailStr
    full_name: Optional[str]
    role: str
    matric_no: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"