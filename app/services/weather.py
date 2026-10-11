import logging
from datetime import date, datetime
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings
from app.schemas.weather import (
    WeatherCurrent,
    WeatherDailyForecast,
    WeatherReport,
)

logger = logging.getLogger(__name__)

# WMO Weather interpretation codes (WW)
WMO_CODE_MAP: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    62: "Moderate rain",
    63: "Moderate rain",
    64: "Heavy rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherServiceError(Exception):
    """Base exception for weather service errors."""
    pass


class WeatherLocationNotFoundError(WeatherServiceError):
    """Raised when geocoding fails to locate the requested place."""
    pass


class WeatherProviderError(WeatherServiceError):
    """Raised when the weather API provider returns an error or is unreachable."""
    pass


class WeatherService:
    """Service to retrieve real-world weather data and forecasts for gardens."""

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout = timeout_seconds

    def _get_condition_description(self, code: Optional[int]) -> str:
        """Map WMO weather code to descriptive text."""
        if code is None:
            return "Unknown"
        return WMO_CODE_MAP.get(code, f"Weather condition ({code})")

    async def geocode_location(self, location: str) -> Dict[str, Any]:
        """Geocode a city or location name to latitude and longitude.

        Args:
            location: City or region name.

        Returns:
            Dict containing name, latitude, longitude, country.

        Raises:
            WeatherLocationNotFoundError: If no matching location was found.
            WeatherProviderError: On network or API failure.
        """
        location = location.strip()
        if not location:
            raise WeatherLocationNotFoundError("Location name cannot be empty.")

        params = {"name": location, "count": 1, "language": "en", "format": "json"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.GEOCODING_URL, params=params)
                if response.status_code != 200:
                    logger.error(f"Geocoding API failed with status {response.status_code}: {response.text}")
                    raise WeatherProviderError(f"Geocoding provider returned status {response.status_code}.")

                data = response.json()
        except httpx.RequestError as exc:
            logger.error(f"Network error querying geocoding service: {exc}")
            raise WeatherProviderError(f"Network error contacting geocoding service: {exc}") from exc
        except ValueError as exc:
            logger.error(f"Invalid JSON returned by geocoding service: {exc}")
            raise WeatherProviderError("Unexpected response format from geocoding service.") from exc

        results = data.get("results")
        if not results or len(results) == 0:
            raise WeatherLocationNotFoundError(f"Location '{location}' could not be found.")

        best_match = results[0]
        return {
            "name": best_match.get("name", location),
            "country": best_match.get("country", ""),
            "latitude": float(best_match["latitude"]),
            "longitude": float(best_match["longitude"]),
        }

    async def get_weather(self, location: str, forecast_days: int = 3) -> WeatherReport:
        """Fetch current weather and daily forecast for a given location.

        Args:
            location: City or location string (e.g. "Seattle", "London", "Tokyo").
            forecast_days: Number of days of forecast to return (1-7, default 3).

        Returns:
            WeatherReport with structured current and upcoming weather data.

        Raises:
            WeatherLocationNotFoundError: When location cannot be resolved.
            WeatherProviderError: When weather service is down or returns error.
        """
        forecast_days = max(1, min(7, forecast_days))
        geo = await self.geocode_location(location)

        params = {
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": forecast_days,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.FORECAST_URL, params=params)
                if response.status_code != 200:
                    logger.error(f"Forecast API failed with status {response.status_code}: {response.text}")
                    raise WeatherProviderError(f"Weather API returned status {response.status_code}.")

                data = response.json()
        except httpx.RequestError as exc:
            logger.error(f"Network error querying weather service: {exc}")
            raise WeatherProviderError(f"Network error contacting weather service: {exc}") from exc
        except ValueError as exc:
            logger.error(f"Invalid JSON returned by weather service: {exc}")
            raise WeatherProviderError("Unexpected response format from weather service.") from exc

        return self._parse_weather_response(geo=geo, data=data)

    def _parse_weather_response(self, geo: Dict[str, Any], data: Dict[str, Any]) -> WeatherReport:
        """Parse raw Open-Meteo response into domain WeatherReport schema."""
        current_data = data.get("current", {})
        daily_data = data.get("daily", {})

        # Current weather
        curr_temp = float(current_data.get("temperature_2m", 0.0))
        curr_hum = int(current_data.get("relative_humidity_2m", 0))
        curr_precip = float(current_data.get("precipitation", 0.0))
        curr_code = current_data.get("weather_code")

        current = WeatherCurrent(
            temperature_c=curr_temp,
            humidity_percent=curr_hum,
            precipitation_mm=curr_precip,
            condition=self._get_condition_description(curr_code),
        )

        # Parse daily forecasts
        dates = daily_data.get("time", [])
        temp_maxs = daily_data.get("temperature_2m_max", [])
        temp_mins = daily_data.get("temperature_2m_min", [])
        precip_sums = daily_data.get("precipitation_sum", [])
        precip_probs = daily_data.get("precipitation_probability_max", [])
        weather_codes = daily_data.get("weather_code", [])

        forecast_list = []
        for i in range(len(dates)):
            d_date = date.fromisoformat(dates[i])
            t_max = float(temp_maxs[i]) if i < len(temp_maxs) and temp_maxs[i] is not None else 0.0
            t_min = float(temp_mins[i]) if i < len(temp_mins) and temp_mins[i] is not None else 0.0
            p_sum = float(precip_sums[i]) if i < len(precip_sums) and precip_sums[i] is not None else 0.0
            p_prob = int(precip_probs[i]) if i < len(precip_probs) and precip_probs[i] is not None else 0
            code = weather_codes[i] if i < len(weather_codes) else None

            forecast_list.append(
                WeatherDailyForecast(
                    date=d_date,
                    temp_max_c=t_max,
                    temp_min_c=t_min,
                    precipitation_sum_mm=p_sum,
                    precipitation_probability_max=p_prob,
                    condition=self._get_condition_description(code),
                )
            )

        today_forecast = forecast_list[0] if forecast_list else WeatherDailyForecast(
            date=date.today(),
            temp_max_c=curr_temp,
            temp_min_c=curr_temp,
            precipitation_sum_mm=curr_precip,
            precipitation_probability_max=0,
            condition=current.condition,
        )

        tomorrow_forecast = forecast_list[1] if len(forecast_list) > 1 else None

        is_rain_today = today_forecast.precipitation_probability_max >= 40 or today_forecast.precipitation_sum_mm >= 1.0
        is_rain_tomorrow = (
            tomorrow_forecast is not None
            and (tomorrow_forecast.precipitation_probability_max >= 40 or tomorrow_forecast.precipitation_sum_mm >= 1.0)
        )

        # Build garden-focused summary string
        summary_parts = [f"Current: {current.condition}, {current.temperature_c}°C, {current.humidity_percent}% humidity."]
        if is_rain_today:
            summary_parts.append(
                f"Rain likely today ({today_forecast.precipitation_probability_max}% chance, {today_forecast.precipitation_sum_mm}mm)."
            )
        else:
            summary_parts.append(f"Today: {today_forecast.condition}, {today_forecast.temp_max_c}°C / {today_forecast.temp_min_c}°C.")

        if tomorrow_forecast:
            if is_rain_tomorrow:
                summary_parts.append(
                    f"Rain expected tomorrow ({tomorrow_forecast.precipitation_probability_max}% chance, {tomorrow_forecast.precipitation_sum_mm}mm)."
                )
            else:
                summary_parts.append(f"Tomorrow: {tomorrow_forecast.condition}, {tomorrow_forecast.temp_max_c}°C.")

        display_name = f"{geo['name']}, {geo['country']}" if geo.get("country") else geo["name"]

        return WeatherReport(
            location=display_name,
            latitude=geo["latitude"],
            longitude=geo["longitude"],
            current=current,
            today=today_forecast,
            tomorrow=tomorrow_forecast,
            forecast=forecast_list,
            is_rain_expected_today=is_rain_today,
            is_rain_expected_tomorrow=is_rain_tomorrow,
            summary=" ".join(summary_parts),
        )


weather_service = WeatherService()

