from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class GardenBase(BaseModel):
    """Base schema for garden information."""

    name: str = Field(..., min_length=1, max_length=150, description="Name of the garden")
    location: Optional[str] = Field(None, max_length=255, description="Location used for weather data")
    garden_type: Optional[str] = Field(None, max_length=100, description="Balcony, Backyard, Raised Bed, etc.")
    sunlight: Optional[str] = Field(None, max_length=100, description="Sunlight exposure conditions")
    notes: Optional[str] = None


class GardenCreate(GardenBase):
    """Schema for creating a new garden."""

    user_id: int = Field(..., description="Owner user ID")


class GardenUpdate(BaseModel):
    """Schema for updating garden details."""

    name: Optional[str] = Field(None, min_length=1, max_length=150)
    location: Optional[str] = None
    garden_type: Optional[str] = None
    sunlight: Optional[str] = None
    notes: Optional[str] = None


class GardenResponse(GardenBase):
    """Schema for garden response."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

