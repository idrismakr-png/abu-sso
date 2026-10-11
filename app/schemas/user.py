from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Fields required to create a new user (admin-only in production)."""

    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: str = Field(default="student")
    matric_no: str = Field(min_length=3, max_length=50, description="Matric or staff number")


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
    """Login credentials. Authentication is by matric/staff number, not email."""

    matric_no: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"