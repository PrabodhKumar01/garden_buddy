import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.services.weather import (
    WeatherLocationNotFoundError,
    WeatherProviderError,
    WeatherService,
)
from app.tools.weather_tool import WEATHER_TOOL_DEFINITION, execute_weather_tool

MOCK_GEOCODING_RESPONSE = {
    "results": [
        {
            "name": "San Francisco",
            "country": "United States",
            "latitude": 37.7749,
            "longitude": -122.4194,
        }
    ]
}

MOCK_FORECAST_RESPONSE = {
    "current": {
        "temperature_2m": 18.5,
        "relative_humidity_2m": 72,
        "precipitation": 0.0,
        "weather_code": 1,
    },
    "daily": {
        "time": ["2026-10-10", "2026-10-11", "2026-10-12"],
        "temperature_2m_max": [20.0, 16.0, 17.5],
        "temperature_2m_min": [12.0, 11.0, 10.5],
        "precipitation_sum": [0.0, 8.5, 0.2],
        "precipitation_probability_max": [10, 80, 20],
        "weather_code": [1, 63, 2],
    },
}


class TestWeatherIntegration(unittest.IsolatedAsyncioTestCase):
    """Test suite covering Phase 4 requirements."""

    def setUp(self):
        self.client = TestClient(app)
        self.weather_service = WeatherService(timeout_seconds=5.0)

    # 1. Valid Weather Request
    @patch("httpx.AsyncClient.get")
    async def test_valid_weather_request(self, mock_get):
        mock_resp_geo = MagicMock()
        mock_resp_geo.status_code = 200
        mock_resp_geo.json.return_value = MOCK_GEOCODING_RESPONSE

        mock_resp_forecast = MagicMock()
        mock_resp_forecast.status_code = 200
        mock_resp_forecast.json.return_value = MOCK_FORECAST_RESPONSE

        mock_get.side_effect = [mock_resp_geo, mock_resp_forecast]

        report = await self.weather_service.get_weather(location="San Francisco", forecast_days=3)

        self.assertIn("San Francisco", report.location)
        self.assertEqual(report.current.temperature_c, 18.5)
        self.assertEqual(report.current.humidity_percent, 72)
        self.assertEqual(report.current.condition, "Mainly clear")
        self.assertFalse(report.is_rain_expected_today)
        self.assertTrue(report.is_rain_expected_tomorrow)
        self.assertEqual(len(report.forecast), 3)
        self.assertIn("Rain expected tomorrow", report.summary)

    # 2. Invalid Location
    @patch("httpx.AsyncClient.get")
    async def test_invalid_location(self, mock_get):
        mock_resp_geo = MagicMock()
        mock_resp_geo.status_code = 200
        mock_resp_geo.json.return_value = {"results": []}
        mock_get.return_value = mock_resp_geo

        with self.assertRaises(WeatherLocationNotFoundError):
            await self.weather_service.get_weather(location="NonExistentCityXYZ123")

    # 3. Weather Provider Failure (500 or network error)
    @patch("httpx.AsyncClient.get")
    async def test_weather_provider_network_failure(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("Connection refused by provider")

        with self.assertRaises(WeatherProviderError):
            await self.weather_service.get_weather(location="San Francisco")

    @patch("httpx.AsyncClient.get")
    async def test_weather_provider_server_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_get.return_value = mock_resp

        with self.assertRaises(WeatherProviderError):
            await self.weather_service.get_weather(location="San Francisco")

    # 4. Unexpected / Malformed API Response
    @patch("httpx.AsyncClient.get")
    async def test_unexpected_api_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_resp

        with self.assertRaises(WeatherProviderError):
            await self.weather_service.get_weather(location="San Francisco")

    # 5. Empty location validation
    async def test_empty_location_validation(self):
        with self.assertRaises(WeatherLocationNotFoundError):
            await self.weather_service.get_weather(location="   ")

    # 6. Tool Interface & Graceful Failure Handling (DevRelay MCP)
    @patch("httpx.AsyncClient.get")
    async def test_weather_tool_success(self, mock_get):
        mock_resp_geo = MagicMock()
        mock_resp_geo.status_code = 200
        mock_resp_geo.json.return_value = MOCK_GEOCODING_RESPONSE

        mock_resp_forecast = MagicMock()
        mock_resp_forecast.status_code = 200
        mock_resp_forecast.json.return_value = MOCK_FORECAST_RESPONSE

        mock_get.side_effect = [mock_resp_geo, mock_resp_forecast]

        result = await execute_weather_tool(location="San Francisco", days=3)
        self.assertTrue(result["success"])
        self.assertIsNone(result["error"])
        self.assertTrue(result["gardening_signals"]["is_rain_expected_tomorrow"])
        self.assertEqual(result["gardening_signals"]["current_temperature_c"], 18.5)

    @patch("httpx.AsyncClient.get")
    async def test_weather_tool_graceful_error_handling(self, mock_get):
        mock_resp_geo = MagicMock()
        mock_resp_geo.status_code = 200
        mock_resp_geo.json.return_value = {"results": []}
        mock_get.return_value = mock_resp_geo

        result = await execute_weather_tool(location="Atlantis Unknown")
        self.assertFalse(result["success"])
        self.assertIn("Location not found", result["error"])
        self.assertIsNone(result["gardening_signals"])

    # 7. Endpoint Tests
    @patch("httpx.AsyncClient.get")
    def test_forecast_endpoint_success(self, mock_get):
        mock_resp_geo = MagicMock()
        mock_resp_geo.status_code = 200
        mock_resp_geo.json.return_value = MOCK_GEOCODING_RESPONSE

        mock_resp_forecast = MagicMock()
        mock_resp_forecast.status_code = 200
        mock_resp_forecast.json.return_value = MOCK_FORECAST_RESPONSE

        mock_get.side_effect = [mock_resp_geo, mock_resp_forecast]

        resp = self.client.get("/api/v1/weather/forecast?location=San+Francisco")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("San Francisco", data["location"])
        self.assertIn("current", data)
        self.assertIn("today", data)
        self.assertIn("tomorrow", data)

    @patch("httpx.AsyncClient.get")
    def test_forecast_endpoint_not_found(self, mock_get):
        mock_resp_geo = MagicMock()
        mock_resp_geo.status_code = 200
        mock_resp_geo.json.return_value = {"results": []}
        mock_get.return_value = mock_resp_geo

        resp = self.client.get("/api/v1/weather/forecast?location=FakePlace12345")
        self.assertEqual(resp.status_code, 404)

    def test_weather_tool_spec_endpoint(self):
        resp = self.client.get("/api/v1/weather/tool/spec")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["name"], "get_weather_forecast")
        self.assertIn("location", resp.json()["parameters"]["properties"])


if __name__ == "__main__":
    unittest.main()

