from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    """Base schema for user data."""

    username: str = Field(..., min_length=2, max_length=100, description="Unique username")
    email: Optional[str] = Field(None, max_length=255, description="Optional user email")


class UserCreate(UserBase):
    """Schema for registering or creating a user."""
    pass


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
