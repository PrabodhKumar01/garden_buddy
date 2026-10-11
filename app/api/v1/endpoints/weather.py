from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.weather import WeatherReport
from app.services.weather import (
    WeatherLocationNotFoundError,
    WeatherProviderError,
    weather_service,
)
from app.tools.weather_tool import WEATHER_TOOL_DEFINITION, execute_weather_tool

router = APIRouter()


@router.get("/forecast", response_model=WeatherReport)
async def get_weather_forecast(
    location: str = Query(..., min_length=1, max_length=200, description="City or region name for the garden"),
    days: int = Query(3, ge=1, le=7, description="Forecast days (1 to 7)")
):
    """Retrieve structured weather report and multi-day forecast for a garden location."""
    try:
        return await weather_service.get_weather(location=location, forecast_days=days)
    except WeatherLocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )
    except WeatherProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Weather service unavailable: {str(exc)}"
        )


@router.get("/tool/spec")
async def get_weather_tool_spec() -> Dict[str, Any]:
    """Retrieve the DevRelay MCP / Thinking Machines tool specification for weather."""
    return WEATHER_TOOL_DEFINITION


@router.post("/tool/execute")
async def execute_tool_endpoint(
    location: str = Query(..., min_length=1, description="Location to query"),
    days: int = Query(3, ge=1, le=7, description="Number of forecast days")
) -> Dict[str, Any]:
    """Execute the weather tool directly via MCP-compatible endpoint."""
    return await execute_weather_tool(location=location, days=days)

