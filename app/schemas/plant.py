from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PlantBase(BaseModel):
    """Base schema for plant details."""

    name: str = Field(..., min_length=1, max_length=100, description="Plant name (e.g. Tomato, Coriander)")
    species: Optional[str] = Field(None, max_length=150, description="Species or cultivar")
    date_planted: Optional[date] = None
    location_in_garden: Optional[str] = Field(None, max_length=150, description="Plot or container label")
    notes: Optional[str] = None


class PlantCreate(PlantBase):
    """Schema for adding a plant to a garden."""

    garden_id: int = Field(..., description="ID of the garden where the plant is placed")


class PlantUpdate(BaseModel):
    """Schema for updating plant information."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    species: Optional[str] = None
    date_planted: Optional[date] = None
    location_in_garden: Optional[str] = None
    notes: Optional[str] = None


class PlantResponse(PlantBase):
    """Schema for plant response."""

    id: int
    garden_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

