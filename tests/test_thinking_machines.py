import unittest
from unittest.mock import AsyncMock, patch
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import httpx

from app.core.database import Base, get_db
from app.main import app as fastapi_app
from app.models.garden import Garden
from app.models.plant import Plant
from app.models.user import User
from app.schemas.ai_plan import GeneratePlanRequest
from app.services.context_builder import context_builder
from app.services.thinking_machines import ThinkingMachinesService


class TestThinkingMachinesAI(unittest.IsolatedAsyncioTestCase):
    """Test suite for Phase 7: Thinking Machines AI integration and daily plan generation."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        import app.models  # noqa: F401
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestingSessionLocal()

        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        fastapi_app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(fastapi_app)

        # Create baseline user and garden
        user = User(username="gardener_sam", email="sam@example.com")
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        self.user = user

        garden = Garden(
            user_id=user.id,
            name="Backyard Oasis",
            location="Seattle",
            garden_type="Raised Bed",
            sunlight="Full Sun"
        )
        self.db.add(garden)
        self.db.commit()
        self.db.refresh(garden)
        self.garden = garden

        plant = Plant(
            garden_id=garden.id,
            name="Roma Tomato",
            species="Solanum lycopersicum",
            location_in_garden="Bed 1"
        )
        self.db.add(plant)
        self.db.commit()
        self.db.refresh(plant)
        self.plant = plant

        self.service = ThinkingMachinesService()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        fastapi_app.dependency_overrides.clear()

    # 1. Context Assembly: 5 Pillars
    @patch("app.services.context_builder.devrelay_mcp_client.invoke_tool")
    async def test_context_builder_assembly(self, mock_invoke_tool):
        from app.schemas.mcp import ToolExecutionResponse
        mock_invoke_tool.return_value = ToolExecutionResponse(
            tool_name="get_weather_forecast",
            success=True,
            data={
                "current": {"condition": "Clear"},
                "gardening_signals": {
                    "summary": "Sunny today, rain expected tomorrow.",
                    "is_rain_expected_today": False,
                    "is_rain_expected_tomorrow": True,
                    "current_temperature_c": 21.0
                }
            },
            data_transmitted={"location": "Seattle", "days": 3}
        )

        context = await context_builder.build_context(
            db=self.db,
            garden_id=self.garden.id,
            target_date=date.today()
        )

        prompt = context.to_prompt_text()
        self.assertIn("1. GARDEN STATE", prompt)
        self.assertIn("Backyard Oasis", prompt)
        self.assertIn("2. PLANTS IN GARDEN", prompt)
        self.assertIn("Roma Tomato", prompt)
        self.assertIn("3. WEATHER CONTEXT", prompt)
        self.assertIn("4. RELEVANT GARDENING KNOWLEDGE (RAG)", prompt)
        self.assertIn("5. PERSISTENT USER MEMORY (BACKBOARD)", prompt)

    # 2. AI Integration & Cloud API Success
    @patch("httpx.AsyncClient.post")
    @patch("app.services.context_builder.devrelay_mcp_client.invoke_tool")
    async def test_thinking_machines_cloud_success(self, mock_tool, mock_post):
        from app.schemas.mcp import ToolExecutionResponse
        from unittest.mock import MagicMock
        mock_tool.return_value = ToolExecutionResponse(
            tool_name="get_weather_forecast",
            success=False,
            error="offline",
            data_transmitted={}
        )
        self.service.api_key = "test-ai-key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"weather_summary": "Mild weather.", "reasoning_notes": "Rain coming.", '
                            '"outdoor_motivation": "Go garden!", "action_items": ['
                            '{"title": "Check tomato soil", "description": "Look for dryness.", "category": "watering", '
                            '"plant_name": "Roma Tomato", "priority": "high"}]}'
                        )
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        plan = await self.service.generate_daily_plan(
            db=self.db,
            garden_id=self.garden.id,
            save_tasks_to_db=True
        )

        self.assertEqual(plan.generated_by, "thinking_machines")
        self.assertEqual(len(plan.action_items), 1)
        self.assertEqual(plan.action_items[0].title, "Check tomato soil")
        self.assertEqual(plan.action_items[0].plant_id, self.plant.id)

    # 3. AI Service Unavailable / Fallback
    @patch("httpx.AsyncClient.post")
    async def test_ai_service_unavailable_fallback(self, mock_post):
        self.service.api_key = "test-ai-key"
        mock_post.side_effect = httpx.ConnectError("Service down")

        plan = await self.service.generate_daily_plan(
            db=self.db,
            garden_id=self.garden.id,
            save_tasks_to_db=False
        )

        self.assertEqual(plan.generated_by, "rule_engine_fallback")
        self.assertGreater(len(plan.action_items), 0)
        self.assertIn("touch grass", plan.outdoor_motivation.lower())

    # 4. Invalid AI Response Handling
    @patch("httpx.AsyncClient.post")
    async def test_invalid_ai_response_handling(self, mock_post):
        self.service.api_key = "test-ai-key"
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "This is non-JSON unstructured text."}}]
        }
        mock_post.return_value = mock_resp

        plan = await self.service.generate_daily_plan(
            db=self.db,
            garden_id=self.garden.id,
            save_tasks_to_db=False
        )

        self.assertEqual(plan.generated_by, "rule_engine_fallback")

    # 5. Timeout Handling
    @patch("httpx.AsyncClient.post")
    async def test_ai_timeout_handling(self, mock_post):
        self.service.api_key = "test-ai-key"
        mock_post.side_effect = httpx.TimeoutException("Request timed out")

        plan = await self.service.generate_daily_plan(
            db=self.db,
            garden_id=self.garden.id,
            save_tasks_to_db=False
        )

        self.assertEqual(plan.generated_by, "rule_engine_fallback")

    # 6. Missing Context Handling (Empty garden with no plants or location)
    async def test_missing_context_handling(self):
        empty_garden = Garden(user_id=self.user.id, name="Empty Plot")
        self.db.add(empty_garden)
        self.db.commit()
        self.db.refresh(empty_garden)

        plan = await self.service.generate_daily_plan(
            db=self.db,
            garden_id=empty_garden.id,
            save_tasks_to_db=False
        )

        self.assertEqual(plan.generated_by, "rule_engine_fallback")
        titles = [item.title.lower() for item in plan.action_items]
        self.assertTrue(any("prepare" in t or "choose" in t for t in titles))

    # 7. Daily Plan REST Endpoints
    def test_daily_plan_endpoints(self):
        # POST endpoint
        post_res = self.client.post(
            "/api/v1/ai/daily-plan",
            json={"garden_id": self.garden.id, "save_tasks_to_db": True}
        )
        self.assertEqual(post_res.status_code, 200)
        data = post_res.json()
        self.assertEqual(data["garden_id"], self.garden.id)
        self.assertGreater(len(data["action_items"]), 0)
        self.assertIn("outdoor_motivation", data)

        # GET endpoint
        get_res = self.client.get(f"/api/v1/ai/daily-plan/{self.garden.id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["garden_id"], self.garden.id)


if __name__ == "__main__":
    unittest.main()

