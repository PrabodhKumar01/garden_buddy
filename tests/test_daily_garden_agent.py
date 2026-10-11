import unittest
from unittest.mock import AsyncMock, patch
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.crud.crud_task import task_crud
from app.main import app as fastapi_app
from app.models.garden import Garden
from app.models.plant import Plant
from app.models.user import User
from app.schemas.mcp import ToolExecutionResponse
from app.schemas.memory import MemoryCreate, MemoryType
from app.services.backboard import backboard_service
from app.services.daily_garden_agent import daily_garden_agent


class TestDailyGardenAgent(unittest.IsolatedAsyncioTestCase):
    """Test suite for Phase 9: Daily Garden Agent orchestration and plan content."""

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

        # 1. Setup User
        user = User(username="garden_enthusiast", email="grower@example.com")
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        self.user = user

        # 2. Setup Garden
        garden = Garden(
            user_id=user.id,
            name="Sunny Urban Plot",
            location="Chicago",
            garden_type="Backyard",
            sunlight="Full Sun"
        )
        self.db.add(garden)
        self.db.commit()
        self.db.refresh(garden)
        self.garden = garden

        # 3. Setup Plants (Tomato and Coriander)
        p1 = Plant(garden_id=garden.id, name="Tomato", species="Roma", location_in_garden="Bed 1")
        p2 = Plant(garden_id=garden.id, name="Coriander", species="Cilantro", location_in_garden="Bed 2")
        self.db.add_all([p1, p2])
        self.db.commit()
        self.db.refresh(p1)
        self.db.refresh(p2)
        self.plants = [p1, p2]

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        fastapi_app.dependency_overrides.clear()

    # Phase 9.1: Complete 8-Step Daily Plan Generation
    @patch("app.mcp.devrelay_client.devrelay_mcp_client.invoke_tool")
    async def test_full_daily_plan_generation_workflow(self, mock_tool):
        # Setup memory in Backboard
        await backboard_service.create_memory(
            MemoryCreate(
                user_id=self.user.id,
                garden_id=self.garden.id,
                memory_type=MemoryType.PREFERENCE,
                content="Prefers organic pest control and morning gardening",
                importance=4
            )
        )
        await backboard_service.create_memory(
            MemoryCreate(
                user_id=self.user.id,
                garden_id=self.garden.id,
                memory_type=MemoryType.OBSERVATION,
                content="Tomatoes previously showed lower leaf yellowing under heavy watering",
                importance=5
            )
        )

        # Mock weather tool response indicating rain tomorrow
        mock_tool.return_value = ToolExecutionResponse(
            tool_name="get_weather_forecast",
            success=True,
            data={
                "current": {"temperature_c": 23.0, "condition": "Mainly clear"},
                "gardening_signals": {
                    "summary": "Warm today (23°C). Rain expected tomorrow (75% probability, 9mm).",
                    "is_rain_expected_today": False,
                    "is_rain_expected_tomorrow": True,
                    "current_temperature_c": 23.0
                }
            },
            data_transmitted={"location": "Chicago", "days": 3}
        )

        plan = await daily_garden_agent.execute_daily_workflow(
            db=self.db,
            garden_id=self.garden.id,
            target_date=date.today(),
            save_to_database=True
        )

        # Assertions covering Phase 9.1
        self.assertEqual(plan.garden_id, self.garden.id)
        self.assertEqual(plan.garden_name, "Sunny Urban Plot")
        self.assertIn("Chicago", plan.weather_summary)
        self.assertGreaterEqual(len(plan.action_items), 2)
        self.assertIn("touch grass", plan.outdoor_motivation.lower())

        # Verify tasks were persisted to garden_tasks table
        saved_tasks = task_crud.get_todays_tasks(db=self.db, garden_id=self.garden.id)
        self.assertGreater(len(saved_tasks), 0)
        self.assertEqual(saved_tasks[0].source, "ai_generated")

    # Phase 9.2: Real-World Action Content & Markdown Presentation
    @patch("app.mcp.devrelay_client.devrelay_mcp_client.invoke_tool")
    async def test_plan_content_real_world_actions_and_markdown(self, mock_tool):
        mock_tool.return_value = ToolExecutionResponse(
            tool_name="get_weather_forecast",
            success=True,
            data={
                "current": {"temperature_c": 20.0, "condition": "Clear"},
                "gardening_signals": {
                    "summary": "Clear sky today. Rain expected tomorrow.",
                    "is_rain_expected_today": False,
                    "is_rain_expected_tomorrow": True,
                    "current_temperature_c": 20.0
                }
            },
            data_transmitted={"location": "Chicago", "days": 3}
        )

        plan = await daily_garden_agent.execute_daily_workflow(
            db=self.db,
            garden_id=self.garden.id,
            save_to_database=False
        )

        # Check action item quality: concrete categories and actions
        categories = [item.category for item in plan.action_items]
        self.assertTrue("watering" in categories or "harvest" in categories or "inspection" in categories)

        # Test Markdown formatting
        md_text = daily_garden_agent.format_plan_as_markdown(plan)
        self.assertIn("# 🌱 Today's Garden Plan — Sunny Urban Plot", md_text)
        self.assertIn("Recommended Outdoor Actions", md_text)
        self.assertIn("Touch Grass", md_text)

    # API Endpoints
    @patch("app.mcp.devrelay_client.devrelay_mcp_client.invoke_tool", new_callable=AsyncMock)
    def test_agent_api_endpoints(self, mock_tool):
        mock_tool.return_value = ToolExecutionResponse(
            tool_name="get_weather_forecast",
            success=True,
            data={
                "current": {"temperature_c": 22.0, "condition": "Clear"},
                "gardening_signals": {
                    "summary": "Clear sky today.",
                    "is_rain_expected_today": False,
                    "is_rain_expected_tomorrow": False,
                    "current_temperature_c": 22.0
                }
            },
            data_transmitted={"location": "Chicago", "days": 3}
        )

        # POST /api/v1/agent/plan
        post_res = self.client.post(
            "/api/v1/agent/plan",
            json={"garden_id": self.garden.id, "save_tasks_to_db": True}
        )
        self.assertEqual(post_res.status_code, 200)
        self.assertEqual(post_res.json()["garden_id"], self.garden.id)

        # GET /api/v1/agent/plan/{garden_id}?format_markdown=true
        get_res = self.client.get(f"/api/v1/agent/plan/{self.garden.id}?format_markdown=true")
        self.assertEqual(get_res.status_code, 200)
        json_data = get_res.json()
        self.assertIn("plan", json_data)
        self.assertIn("markdown", json_data)
        self.assertIn("# 🌱 Today's Garden Plan", json_data["markdown"])

        # Nonexistent garden returns 404
        err_res = self.client.get("/api/v1/agent/plan/99999")
        self.assertEqual(err_res.status_code, 404)


if __name__ == "__main__":
    unittest.main()

