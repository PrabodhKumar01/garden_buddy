import logging
from typing import Any, Dict

from app.services.weather import (
    WeatherLocationNotFoundError,
    WeatherProviderError,
    WeatherServiceError,
    weather_service,
)

logger = logging.getLogger(__name__)

# Standard Tool Definition for DevRelay MCP / Thinking Machines
WEATHER_TOOL_DEFINITION: Dict[str, Any] = {
    "name": "get_weather_forecast",
    "description": (
        "Retrieve current weather and upcoming forecast for a garden's location. "
        "Use this tool to inspect temperature, rain probability, and upcoming rainfall before "
        "recommending outdoor gardening tasks such as watering, planting, or harvesting."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City or geographic location of the garden (e.g., 'San Francisco', 'London', 'Kyoto')."
            },
            "days": {
                "type": "integer",
                "description": "Number of forecast days to look ahead (1 to 7, default is 3).",
                "default": 3
            }
        },
        "required": ["location"]
    }
}


async def execute_weather_tool(location: str, days: int = 3) -> Dict[str, Any]:
    """Execute the weather tool and return structured context for the AI reasoning agent.

    This function handles errors gracefully so that an unavailable weather service or
    unrecognized location does not crash the agent's reasoning loop.

    Args:
        location: Target garden location.
        days: Forecast days count (default 3).

    Returns:
        Dict containing success status, weather report data or error message,
        and distilled gardening weather signals.
    """
    logger.info(f"Executing weather tool for location '{location}' (days={days})")
    try:
        report = await weather_service.get_weather(location=location, forecast_days=days)
        return {
            "success": True,
            "location": report.location,
            "current": report.current.model_dump(),
            "today": report.today.model_dump(),
            "tomorrow": report.tomorrow.model_dump() if report.tomorrow else None,
            "forecast": [f.model_dump() for f in report.forecast],
            "gardening_signals": {
                "is_rain_expected_today": report.is_rain_expected_today,
                "is_rain_expected_tomorrow": report.is_rain_expected_tomorrow,
                "current_temperature_c": report.current.temperature_c,
                "summary": report.summary,
            },
            "error": None
        }
    except WeatherLocationNotFoundError as exc:
        logger.warning(f"Weather tool location not found: {exc}")
        return {
            "success": False,
            "location": location,
            "error": f"Location not found: {str(exc)}",
            "gardening_signals": None
        }
    except WeatherProviderError as exc:
        logger.error(f"Weather provider error in tool: {exc}")
        return {
            "success": False,
            "location": location,
            "error": f"Weather service temporarily unavailable: {str(exc)}",
            "gardening_signals": None
        }
    except Exception as exc:
        logger.exception(f"Unexpected error executing weather tool: {exc}")
        return {
            "success": False,
            "location": location,
            "error": f"Failed to retrieve weather data: {str(exc)}",
            "gardening_signals": None
        }

