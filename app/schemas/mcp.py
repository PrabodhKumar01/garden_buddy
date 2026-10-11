import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class ToolDecision(BaseModel):
    """Represents the AI agent's decision on whether an external tool is required."""

    needs_weather: bool = Field(..., description="Whether the weather tool should be invoked")
    reason: str = Field(..., description="Agent rationale for calling or skipping the tool")
    location: Optional[str] = Field(None, description="Sanitized location to pass to the tool if needed")


class WeatherToolInput(BaseModel):
    """Validated and sanitized input payload for the weather tool."""

    location: str = Field(..., min_length=1, max_length=100, description="City or location name")
    days: int = Field(default=3, ge=1, le=7, description="Forecast days (1 to 7)")

    @field_validator("location")
    @classmethod
    def sanitize_location(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Location cannot be empty or whitespace only.")
        # Reject potential command injection or script characters
        if re.search(r"[<>{}\$;&|`\\]", clean):
            raise ValueError("Location contains invalid or unsafe characters.")
        return clean


class ToolExecutionResponse(BaseModel):
    """Standardized result returned by the DevRelay MCP tool execution layer."""

    tool_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    data_transmitted: Dict[str, Any] = Field(
        ...,
        description="Public view of data sent to the tool to verify no personal info or secrets leaked"
    )

