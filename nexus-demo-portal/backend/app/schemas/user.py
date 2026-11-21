"""Pydantic schemas for user accounts, credentials, and authentication tokens."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserBase(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, description="Valid email address")
    full_name: str = Field(..., min_length=2, max_length=255)


class UserRegister(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="Password must be at least 8 characters")


class UserLogin(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX)
    password: str = Field(..., min_length=1)


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
