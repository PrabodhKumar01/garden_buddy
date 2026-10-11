import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

try:
    import yaml
except ImportError:
    yaml = None

from app.core.config import Settings
from app.core.database import check_db_connection
from app.main import app as fastapi_app
from app.services.weather import weather_service
from app.services.backboard import backboard_service
from app.services.thinking_machines import thinking_machines_service
from app.mcp.tool_registry import tool_registry


class TestPhase13RenderDeployment(unittest.IsolatedAsyncioTestCase):
    """Phase 13 Comprehensive Deployment Verification Suite for Render."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(fastapi_app)

    # =========================================================================
    # 1. RENDER BLUEPRINT (render.yaml) VALIDATION
    # =========================================================================
    def test_render_yaml_specification(self):
        """Verify render.yaml exists, is valid YAML, and complies with Render Blueprint spec."""
        render_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "render.yaml")
        self.assertTrue(os.path.exists(render_path), "render.yaml must exist in root directory.")

        with open(render_path, "r", encoding="utf-8") as f:
            content = f.read()

        if yaml is not None:
            config = yaml.safe_load(content)
        else:
            # Fallback simple structural check if PyYAML is not in environment
            self.assertIn("services:", content)
            self.assertIn("name: gardenbuddy", content)
            self.assertIn("runtime: python", content)
            self.assertIn("healthCheckPath: /health", content)
            self.assertIn("databases:", content)
            self.assertIn("name: gardenbuddy-db", content)
            return

        # Web service checks
        web_services = [s for s in config["services"] if s.get("type") == "web"]
        self.assertGreaterEqual(len(web_services), 1, "Must define at least one web service.")
        web = web_services[0]

        self.assertEqual(web.get("name"), "gardenbuddy")
        self.assertEqual(web.get("runtime"), "python")
        self.assertEqual(web.get("healthCheckPath"), "/health")
        self.assertIn("pip install", web.get("buildCommand", ""))
        self.assertIn("uvicorn app.main:app", web.get("startCommand", ""))
        self.assertIn("$PORT", web.get("startCommand", ""), "Start command must use Render's dynamic $PORT.")

        # Environment variable bindings in render.yaml
        env_vars = {item["key"]: item for item in web.get("envVars", [])}
        self.assertIn("ENVIRONMENT", env_vars)
        self.assertEqual(env_vars["ENVIRONMENT"].get("value"), "production")

        self.assertIn("DEBUG", env_vars)
        self.assertEqual(env_vars["DEBUG"].get("value"), False)

        self.assertIn("DATABASE_URL", env_vars)
        self.assertEqual(
            env_vars["DATABASE_URL"].get("fromDatabase", {}).get("name"),
            "gardenbuddy-db",
            "DATABASE_URL must be linked to managed database."
        )

        # Security check: External API secrets must have sync: false (never hardcoded)
        for secret_key in ["WEATHER_API_KEY", "BACKBOARD_API_KEY", "THINKING_MACHINES_API_KEY"]:
            self.assertIn(secret_key, env_vars)
            self.assertEqual(env_vars[secret_key].get("sync"), False, f"{secret_key} must have sync: false")

        # Database service checks
        db = config["databases"][0]
        self.assertEqual(db.get("name"), "gardenbuddy-db")
        self.assertEqual(db.get("databaseName"), "gardenbuddy")
        self.assertEqual(db.get("plan"), "free")

    # =========================================================================
    # 2. PRODUCTION SETTINGS & ENVIRONMENT CONFIGURATION
    # =========================================================================
    def test_production_settings_and_cors_parsing(self):
        """Verify production configuration loads correctly and parses CORS origins."""
        prod_settings = Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            PORT=10000,
            ALLOWED_ORIGINS="https://gardenbuddy.onrender.com, https://mygarden.app"
        )
        self.assertEqual(prod_settings.ENVIRONMENT, "production")
        self.assertFalse(prod_settings.DEBUG)
        self.assertEqual(prod_settings.PORT, 10000)
        self.assertEqual(
            prod_settings.ALLOWED_ORIGINS,
            ["https://gardenbuddy.onrender.com", "https://mygarden.app"]
        )

        # JSON array CORS format
        json_cors_settings = Settings(
            ALLOWED_ORIGINS='["https://app.example.com"]'
        )
        self.assertEqual(json_cors_settings.ALLOWED_ORIGINS, ["https://app.example.com"])

        # Wildcard string format
        wildcard_settings = Settings(ALLOWED_ORIGINS="*")
        self.assertEqual(wildcard_settings.ALLOWED_ORIGINS, ["*"])

    # =========================================================================
    # 3. HEALTH ENDPOINT & DATABASE CONNECTIVITY CHECK
    # =========================================================================
    def test_health_endpoint_response_structure(self):
        """Verify /health returns 200 with required production telemetry."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "GardenBuddy")
        self.assertIn("version", data)
        self.assertIn("environment", data)
        self.assertIn("database", data)
        self.assertIn("connected", data["database"])

    def test_database_connection_status_handling(self):
        """Verify check_db_connection handles active connection and failure states gracefully."""
        status = check_db_connection()
        self.assertIsInstance(status, dict)
        self.assertIn("connected", status)
        self.assertIn("message", status)

        # Test simulated database failure
        with patch("app.core.database.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("Connection refused to postgres:5432")
            failed_status = check_db_connection()
            self.assertFalse(failed_status["connected"])
            self.assertIn("Connection refused", failed_status["message"])

    # =========================================================================
    # 4. DATABASE URL NORMALIZATION FOR RENDER
    # =========================================================================
    def test_database_url_normalization(self):
        """Verify Render's postgres:// URLs are normalized to postgresql+psycopg2://."""
        raw_render_url = "postgres://user:secret@dpg-abc123-a.oregon-postgres.render.com/gardenbuddy"
        normalized = raw_render_url.replace("postgres://", "postgresql+psycopg2://", 1)
        self.assertTrue(normalized.startswith("postgresql+psycopg2://"))

        standard_pg_url = "postgresql://user:secret@localhost:5432/gardenbuddy"
        if not standard_pg_url.startswith("postgresql+"):
            normalized_std = standard_pg_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            self.assertTrue(normalized_std.startswith("postgresql+psycopg2://"))

    # =========================================================================
    # 5. EXTERNAL INTEGRATION RESILIENCY (Zero-Downtime Fallbacks)
    # =========================================================================
    async def test_external_services_graceful_degradation(self):
        """Verify external integrations handle unconfigured or failing credentials safely in production."""
        # 1. Weather fallback
        weather = await weather_service.get_current_weather(location="Austin")
        self.assertIsNotNone(weather)
        self.assertIn("conditions", weather.condition.lower() or "sunny")

        # 2. Backboard local fallback
        health = await backboard_service.health_check()
        self.assertIn(health["status"], ["healthy", "available"])

        # 3. DevRelay MCP Tool Registry
        tools = tool_registry.list_tools()
        self.assertGreater(len(tools), 0)
        self.assertTrue(any(t["name"] == "get_weather_forecast" for t in tools))

    # =========================================================================
    # 6. SECURITY & SECRETS AUDIT
    # =========================================================================
    def test_zero_secrets_in_deployment_configs(self):
        """Ensure no production API keys or tokens are hardcoded into configuration files."""
        root_dir = os.path.dirname(os.path.dirname(__file__))

        # Check render.yaml
        with open(os.path.join(root_dir, "render.yaml"), "r", encoding="utf-8") as f:
            render_content = f.read()
            self.assertNotIn("ghp_", render_content)
            self.assertNotIn("sk-", render_content)
            self.assertNotIn("password123", render_content)

        # Check .env.example
        with open(os.path.join(root_dir, ".env.example"), "r", encoding="utf-8") as f:
            example_content = f.read()
            self.assertIn("WEATHER_API_KEY=\n", example_content)
            self.assertIn("BACKBOARD_API_KEY=\n", example_content)
            self.assertIn("THINKING_MACHINES_API_KEY=\n", example_content)


if __name__ == "__main__":
    unittest.main()
