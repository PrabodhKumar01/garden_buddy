from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MemoryType(str, Enum):
    """Types of long-term gardening memory stored in Backboard."""
    PREFERENCE = "preference"      # e.g., "Prefers organic gardening", "Prefers morning gardening"
    OBSERVATION = "observation"    # e.g., "Tomato developed yellow leaves under heavy watering"
    HISTORY = "history"            # e.g., "Planted coriander in Bed 2 in spring"
    HABIT = "habit"                # e.g., "Usually waters early in the morning"


class MemoryBase(BaseModel):
    """Base schema for memory content."""

    memory_type: MemoryType = Field(..., description="Category of memory: preference, observation, history, or habit")
    content: str = Field(..., min_length=3, max_length=1000, description="Useful long-term gardening observation or preference")
    importance: int = Field(default=3, ge=1, le=5, description="Significance weight from 1 (low) to 5 (critical)")
    plant_id: Optional[int] = Field(default=None, description="Optional plant ID associated with this observation")
    garden_id: Optional[int] = Field(default=None, description="Optional garden ID")


class MemoryCreate(MemoryBase):
    """Schema for creating a persistent memory."""

    user_id: int = Field(..., description="ID of the user this memory belongs to")


class MemoryResponse(MemoryBase):
    """Schema for returning a persistent memory record."""

    id: str = Field(..., description="Unique memory ID in Backboard")
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryQueryRequest(BaseModel):
    """Schema for retrieving relevant memories for AI reasoning."""

    user_id: int = Field(..., description="User ID for scoped retrieval")
    garden_id: Optional[int] = Field(default=None, description="Optional garden ID filter")
    query: Optional[str] = Field(default=None, description="Current situation or topic to match against")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of memories to return")


class MemoryQueryResponse(BaseModel):
    """Response containing retrieved memories and formatted context for Thinking Machines."""

    user_id: int
    memories: List[MemoryResponse]
    count: int
    context_text: str = Field(..., description="Formatted bullet points for Thinking Machines prompt context")

