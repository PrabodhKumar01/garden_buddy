from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    """Base schema for garden task data."""

    title: str = Field(..., min_length=1, max_length=200, description="Summary of the outdoor task")
    description: Optional[str] = Field(None, description="Detailed instructions for the gardener")
    category: Optional[str] = Field(None, max_length=50, description="Task category (watering, harvest, etc.)")
    task_date: date = Field(..., description="Target date for this daily garden plan task")
    plant_id: Optional[int] = Field(None, description="Associated plant ID, if plant-specific")
    source: str = Field("ai_generated", max_length=50, description="Origin: ai_generated or user_created")


class TaskCreate(TaskBase):
    """Schema for creating a new garden task."""

    garden_id: int = Field(..., description="ID of the garden to which this task belongs")
    is_completed: bool = Field(False, description="Initial completion state")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    task_date: Optional[date] = None
    is_completed: Optional[bool] = None
    result_notes: Optional[str] = None
    plant_id: Optional[int] = None


class TaskStatusUpdate(BaseModel):
    """Schema for toggling task completion status and optionally recording observations."""

    is_completed: bool = Field(..., description="Set to True when user completed the activity outside")
    result_notes: Optional[str] = Field(None, description="Gardener observations or notes upon completion")


class TaskResponse(TaskBase):
    """Schema for task response payloads."""

    id: int
    garden_id: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    result_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

