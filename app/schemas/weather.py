from datetime import date as dt_date
from typing import List, Optional
from pydantic import BaseModel, Field


class WeatherDailyForecast(BaseModel):
    """Forecast for a single day."""

    date: dt_date = Field(..., description="Forecast date")
    temp_max_c: float = Field(..., description="Maximum temperature in Celsius")
    temp_min_c: float = Field(..., description="Minimum temperature in Celsius")
    precipitation_sum_mm: float = Field(..., description="Total expected precipitation in mm")
    precipitation_probability_max: int = Field(..., ge=0, le=100, description="Peak precipitation probability (0-100%)")
    condition: str = Field(..., description="Weather condition description (e.g. Sunny, Light rain)")


class WeatherCurrent(BaseModel):
    """Current weather observations."""

    temperature_c: float = Field(..., description="Current temperature in Celsius")
    humidity_percent: int = Field(..., ge=0, le=100, description="Relative humidity percentage")
    precipitation_mm: float = Field(..., description="Current precipitation rate in mm")
    condition: str = Field(..., description="Current weather condition")


class WeatherReport(BaseModel):
    """Comprehensive weather report tailored for garden decision making."""

    location: str = Field(..., description="Name of the queried location")
    latitude: float
    longitude: float
    current: WeatherCurrent
    today: WeatherDailyForecast
    tomorrow: Optional[WeatherDailyForecast] = None
    forecast: List[WeatherDailyForecast] = Field(default_factory=list, description="Upcoming daily forecasts")
    is_rain_expected_today: bool = Field(..., description="Whether rain is likely today (prob >= 40% or precip > 1mm)")
    is_rain_expected_tomorrow: bool = Field(..., description="Whether rain is likely tomorrow (prob >= 40% or precip > 1mm)")
    summary: str = Field(..., description="High-level gardening-focused summary of the weather")

