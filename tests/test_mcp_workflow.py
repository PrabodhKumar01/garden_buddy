import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.mcp.devrelay_client import devrelay_mcp_client
from app.mcp.tool_decision import tool_decider
from app.mcp.tool_registry import tool_registry
from app.models.garden import Garden
from app.schemas.mcp import WeatherToolInput


class TestMCPWorkflowAndSafety(unittest.IsolatedAsyncioTestCase):
    """Test suite covering Phase 8: Agent Tool Decision, MCP Workflow, and Tool Safety."""

    def setUp(self):
        self.client = TestClient(app)

    # 1. Tool Decision Logic (Phase 8.1)
    def test_tool_decision_outdoor_garden_with_location(self):
        """Outdoor garden with a location should determine that the weather tool is needed."""
        garden = Garden(id=1, name="Sunny Patio", location="London", garden_type="Container")
        decision = tool_decider.evaluate_weather_need(garden)
        self.assertTrue(decision.needs_weather)
        self.assertEqual(decision.location, "London")
        self.assertIn("Outdoor/exposed garden", decision.reason)

    def test_tool_decision_indoor_garden_skipped(self):
        """Indoor garden should NOT invoke the weather tool."""
        garden = Garden(id=2, name="Living Room Hydroponics", location="Denver", garden_type="Hydroponic")
        decision = tool_decider.evaluate_weather_need(garden)
        self.assertFalse(decision.needs_weather)
        self.assertIsNone(decision.location)
        self.assertIn("indoor", decision.reason.lower())

    def test_tool_decision_missing_location_skipped(self):
        """Garden without location configured should skip the weather tool."""
        garden = Garden(id=3, name="Mystery Plot", location=None, garden_type="Backyard")
        decision = tool_decider.evaluate_weather_need(garden)
        self.assertFalse(decision.needs_weather)
        self.assertIn("no location specified", decision.reason.lower())

    # 2. Tool Safety: Input Verification (Phase 8.3)
    def test_tool_safety_input_verification_valid(self):
        """Valid location and days pass sanitization."""
        validated = WeatherToolInput(location="  Portland, OR  ", days=4)
        self.assertEqual(validated.location, "Portland, OR")
        self.assertEqual(validated.days, 4)

    def test_tool_safety_input_verification_rejects_injection(self):
        """Unsafe or injection characters are strictly rejected."""
        with self.assertRaises(ValueError):
            WeatherToolInput(location="Seattle; cat /etc/passwd")

        with self.assertRaises(ValueError):
            WeatherToolInput(location="<script>alert(1)</script>")

    def test_tool_safety_input_verification_clamps_days(self):
        """Days outside 1-7 range trigger validation errors."""
        with self.assertRaises(ValueError):
            WeatherToolInput(location="Austin", days=10)

        with self.assertRaises(ValueError):
            WeatherToolInput(location="Austin", days=0)

    # 3. Tool Safety: Data Minimization & No Credentials Exposed (Phase 8.3)
    @patch("app.mcp.tool_registry.execute_weather_tool")
    async def test_tool_safety_data_minimization(self, mock_exec):
        mock_exec.return_value = {
            "success": True,
            "location": "Boston",
            "current": {"temperature_c": 22.0},
            "today": {},
            "gardening_signals": {"is_rain_expected_tomorrow": False, "summary": "Clear."},
            "error": None
        }

        # Attempt to pass extraneous personal fields in raw arguments
        raw_payload = {
            "location": "Boston",
            "days": 3,
            "user_email": "gardener@example.com",
            "secret_token": "super_secret_key_123"
        }

        response = await tool_registry.execute_tool("get_weather_forecast", raw_payload)
        self.assertTrue(response.success)
        # Verify that only validated fields were transmitted to the handler
        self.assertIn("location", response.data_transmitted)
        self.assertNotIn("user_email", response.data_transmitted)
        self.assertNotIn("secret_token", response.data_transmitted)

    # 4. Tool Error Handling (Phase 8.3)
    async def test_unregistered_tool_error_handling(self):
        """Calling an unregistered tool fails gracefully without throwing an exception."""
        response = await tool_registry.execute_tool("execute_bash_command", {"command": "ls"})
        self.assertFalse(response.success)
        self.assertIn("Unregistered MCP tool", response.error)

    @patch("app.mcp.tool_registry.execute_weather_tool")
    async def test_tool_provider_error_handled_gracefully(self, mock_exec):
        """Provider failures are captured as clean error responses."""
        mock_exec.return_value = {
            "success": False,
            "error": "Weather API timed out",
            "gardening_signals": None
        }

        response = await tool_registry.execute_tool("get_weather_forecast", {"location": "Chicago"})
        self.assertFalse(response.success)
        self.assertIn("Weather API timed out", response.error)

    # 5. MCP Workflow Execution via Client (Phase 8.2)
    @patch("app.mcp.tool_registry.execute_weather_tool")
    async def test_mcp_workflow_client_dispatch(self, mock_exec):
        mock_exec.return_value = {
            "success": True,
            "location": "Kyoto, Japan",
            "current": {"temperature_c": 19.0, "condition": "Sunny"},
            "today": {},
            "tomorrow": {},
            "gardening_signals": {
                "is_rain_expected_today": False,
                "is_rain_expected_tomorrow": True,
                "summary": "Rain expected tomorrow."
            },
            "error": None
        }

        resp = await devrelay_mcp_client.invoke_tool(
            tool_name="get_weather_forecast",
            arguments={"location": "Kyoto", "days": 3}
        )

        self.assertTrue(resp.success)
        self.assertEqual(resp.tool_name, "get_weather_forecast")
        self.assertIn("gardening_signals", resp.data)
        self.assertTrue(resp.data["gardening_signals"]["is_rain_expected_tomorrow"])

    # 6. REST API Endpoints for MCP
    def test_mcp_endpoints(self):
        # List tools
        list_res = self.client.get("/api/v1/mcp/tools")
        self.assertEqual(list_res.status_code, 200)
        tools = list_res.json()
        self.assertIn("get_weather_forecast", tools)
        self.assertIn("safety_notes", tools["get_weather_forecast"])

        # Execute tool via POST endpoint
        post_res = self.client.post(
            "/api/v1/mcp/execute?tool_name=get_weather_forecast",
            json={"location": "Seattle", "days": 2}
        )
        self.assertEqual(post_res.status_code, 200)
        data = post_res.json()
        self.assertEqual(data["tool_name"], "get_weather_forecast")


if __name__ == "__main__":
    unittest.main()

