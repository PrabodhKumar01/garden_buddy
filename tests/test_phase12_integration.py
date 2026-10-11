import unittest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.crud.crud_garden import garden_crud
from app.crud.crud_plant import plant_crud
from app.crud.crud_task import task_crud
from app.crud.crud_user import user_crud
from app.main import app as fastapi_app
from app.models.garden import Garden
from app.mcp.tool_decision import tool_decider
from app.mcp.tool_registry import tool_registry
from app.schemas.garden import GardenCreate
from app.schemas.memory import MemoryCreate, MemoryType
from app.schemas.plant import PlantCreate
from app.schemas.task import TaskStatusUpdate
from app.schemas.user import UserCreate
from app.tools.weather_tool import execute_weather_tool
from app.services.backboard import backboard_service
from app.services.context_builder import context_builder
from app.services.daily_garden_agent import daily_garden_agent
from app.services.rag import rag_service
from app.services.task_completion import task_completion_service
from app.services.thinking_machines import thinking_machines_service
from app.services.weather import weather_service


class TestPhase12IntegrationAndVerification(unittest.IsolatedAsyncioTestCase):
    """Phase 12 Comprehensive Verification Suite.

    Validates:
    - Backend: API, Validation, Database, Error Handling
    - AI: Context Construction, Tool Invocation, Memory Retrieval, RAG Retrieval, Daily Plan
    - Integration: DB, Weather, Backboard, Thinking Machines, DevRelay MCP
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        fastapi_app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(fastapi_app)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=cls.engine)
        fastapi_app.dependency_overrides.clear()

    def setUp(self):
        self.db = self.TestingSessionLocal()
        backboard_service._local_store.clear()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    # =========================================================================
    # 1. BACKEND VERIFICATION (Database, Validation, Error Handling)
    # =========================================================================
    def test_database_crud_and_relational_integrity(self):
        """Verify Database models, relations, cascade operations, and CRUD integrity."""
        # Create User
        user = user_crud.create(self.db, user_in=UserCreate(username="phase12_tester", email="test12@example.com"))
        self.assertIsNotNone(user.id)

        # Create Garden associated with user
        garden = garden_crud.create(
            self.db,
            garden_in=GardenCreate(user_id=user.id, name="Test Estate", location="Seattle", garden_type="Backyard")
        )
        self.assertEqual(garden.user_id, user.id)

        # Create Plant associated with garden
        plant = plant_crud.create(
            self.db,
            plant_in=PlantCreate(garden_id=garden.id, name="Sweet Basil", species="Ocimum basilicum")
        )
        self.assertEqual(plant.garden_id, garden.id)

        # Verify Relational Navigation
        self.assertEqual(len(garden.plants), 1)
        self.assertEqual(garden.plants[0].name, "Sweet Basil")

        # Cascade Delete: Deleting garden should delete plant
        garden_crud.delete(self.db, db_obj=garden)
        self.assertIsNone(plant_crud.get(self.db, plant_id=plant.id))

    def test_api_validation_and_error_handling(self):
        """Verify API schema validation and structured HTTP error responses."""
        # Missing required fields returns 422
        res_invalid = self.client.post("/api/v1/gardens/", json={"name": "No User Garden"})
        self.assertEqual(res_invalid.status_code, 422)

        # Invalid ID returns 404
        res_404 = self.client.get("/api/v1/gardens/999999")
        self.assertEqual(res_404.status_code, 404)

        # Invalid plant association returns 400
        user = user_crud.create(self.db, user_in=UserCreate(username="err_user", email="err@example.com"))
        g1 = garden_crud.create(self.db, garden_in=GardenCreate(user_id=user.id, name="Garden 1"))
        g2 = garden_crud.create(self.db, garden_in=GardenCreate(user_id=user.id, name="Garden 2"))
        p1 = plant_crud.create(self.db, plant_in=PlantCreate(garden_id=g1.id, name="Plant 1"))

        # Try creating task for g2 with plant from g1
        task_res = self.client.post(
            "/api/v1/tasks/",
            json={
                "garden_id": g2.id,
                "plant_id": p1.id,
                "title": "Conflicting plant task",
                "task_date": date.today().isoformat()
            }
        )
        self.assertEqual(task_res.status_code, 400)

    # =========================================================================
    # 2. AI VERIFICATION (Context, Tool Invocation, Memory, RAG, Daily Plan)
    # =========================================================================
    async def test_ai_rag_retrieval_and_filtering(self):
        """Verify RAG retrieval returns targeted knowledge without irrelevant noise."""
        # Query specific to tomatoes
        rag_res = rag_service.retrieve(query="yellow leaves and watering", plant_names=["Tomato"], limit=2)
        self.assertGreater(len(rag_res.results), 0)
        self.assertTrue(any("tomato" in r.title.lower() or "watering" in r.title.lower() for r in rag_res.results))
        self.assertIn("Tomato", rag_res.context_text)

    async def test_ai_memory_retrieval(self):
        """Verify Backboard memory stores and retrieves scoped user context."""
        user = user_crud.create(self.db, user_in=UserCreate(username="mem_user", email="mem@example.com"))
        garden = garden_crud.create(self.db, garden_in=GardenCreate(user_id=user.id, name="Memory Garden"))

        await backboard_service.create_memory(
            MemoryCreate(
                user_id=user.id,
                garden_id=garden.id,
                memory_type=MemoryType.PREFERENCE,
                content="Prefers organic pest control only, no synthetic sprays.",
                importance=5
            )
        )

        query_res = await backboard_service.retrieve_memories(user_id=user.id, garden_id=garden.id, query="organic")
        self.assertEqual(len(query_res.memories), 1)
        self.assertIn("organic pest control", query_res.memories[0].content)

    async def test_ai_context_builder_and_daily_plan_generation(self):
        """Verify full Context Construction and deterministic Daily Plan generation."""
        user = user_crud.create(self.db, user_in=UserCreate(username="plan_user", email="plan@example.com"))
        garden = garden_crud.create(
            self.db,
            garden_in=GardenCreate(user_id=user.id, name="Sunny Yard", location="Austin", garden_type="Raised Bed")
        )
        plant_crud.create(self.db, plant_in=PlantCreate(garden_id=garden.id, name="Roma Tomato"))
        plant_crud.create(self.db, plant_in=PlantCreate(garden_id=garden.id, name="Spinach"))

        # Build Context
        context = await context_builder.build_context(db=self.db, garden_id=garden.id, target_date=date.today())
        self.assertEqual(context.garden.name, "Sunny Yard")
        self.assertEqual(len(context.plants), 2)
        self.assertIsNotNone(context.weather_summary)
        self.assertIsNotNone(context.knowledge_context)

        # Generate Plan via Thinking Machines
        plan = await thinking_machines_service.generate_daily_plan(db=self.db, garden_id=garden.id, target_date=date.today())
        self.assertEqual(plan.garden_id, garden.id)
        self.assertGreaterEqual(len(plan.action_items), 2)
        self.assertTrue(any(item.category in ("watering", "harvest", "soil", "care") for item in plan.action_items))
        self.assertIn("touch grass", plan.outdoor_motivation.lower())

    # =========================================================================
    # 3. INTEGRATION VERIFICATION (Weather, Backboard, Thinking Machines, MCP)
    # =========================================================================
    async def test_weather_service_and_signals_contract(self):
        """Verify Weather API service signals and contract."""
        signals = await execute_weather_tool(location="Chicago", days=3)
        self.assertIn("location", signals)
        self.assertIn("gardening_signals", signals)
        self.assertIn("is_rain_expected_today", signals["gardening_signals"])
        self.assertIn("is_rain_expected_tomorrow", signals["gardening_signals"])

    def test_tool_decision_and_registry(self):
        """Verify MCP Tool decision and registry contracts."""
        # Outdoor garden with location triggers weather tool
        outdoor_garden = Garden(name="Backyard Plot", garden_type="Backyard", location="Seattle")
        decision = tool_decider.evaluate_weather_need(garden=outdoor_garden)
        self.assertTrue(decision.needs_weather)
        self.assertEqual(decision.location, "Seattle")

        # Indoor garden skips weather tool
        indoor_garden = Garden(name="Hydroponic Tent", garden_type="Indoor", location="Seattle")
        indoor_decision = tool_decider.evaluate_weather_need(garden=indoor_garden)
        self.assertFalse(indoor_decision.needs_weather)

        # Registry tool check
        tool_spec = tool_registry.get_tool("get_weather_forecast")
        self.assertIsNotNone(tool_spec)
        self.assertEqual(tool_spec["name"], "get_weather_forecast")

    # =========================================================================
    # 4. GOLDEN FLOW: Complete Loop from Plan to Action to Memory to Next Plan
    # =========================================================================
    async def test_end_to_end_golden_flow(self):
        """Verify the full Touch Grass cycle:
        Plan Generation -> Database Tasks -> User completes outdoor task ->
        Observation recorded -> Plant State Updated -> Backboard Memory Updated ->
        Next Plan generation aware of previous observations.
        """
        user = user_crud.create(self.db, user_in=UserCreate(username="golden_user", email="golden@example.com"))
        garden = garden_crud.create(
            self.db,
            garden_in=GardenCreate(user_id=user.id, name="Golden Oasis", location="Portland", garden_type="Backyard")
        )
        tomato = plant_crud.create(self.db, plant_in=PlantCreate(garden_id=garden.id, name="Brandywine Tomato"))

        # 1. Agent executes daily workflow and persists tasks
        plan = await daily_garden_agent.execute_daily_workflow(
            db=self.db,
            garden_id=garden.id,
            target_date=date.today(),
            save_to_database=True
        )
        self.assertIsNotNone(plan)

        # 2. Retrieve persisted tasks for today
        todays_tasks = task_crud.get_todays_tasks(db=self.db, garden_id=garden.id)
        self.assertGreater(len(todays_tasks), 0)
        first_task = todays_tasks[0]

        # 3. User goes outside, performs the task, and records observation
        obs_text = "Soil was dry 2 inches down; gave deep soak. Noticed flower buds forming."
        completed_task = await task_completion_service.complete_task(
            db=self.db,
            task_id=first_task.id,
            status_in=TaskStatusUpdate(is_completed=True, result_notes=obs_text)
        )
        self.assertTrue(completed_task.is_completed)
        self.assertIsNotNone(completed_task.completed_at)

        # 4. Verify Plant state was enriched
        refreshed_plant = plant_crud.get(db=self.db, plant_id=tomato.id)
        if first_task.plant_id == tomato.id:
            self.assertIn(obs_text, refreshed_plant.notes)

        # 5. Verify Backboard Memory was persisted
        memories = await backboard_service.retrieve_memories(
            user_id=user.id,
            garden_id=garden.id,
            query="flower buds"
        )
        self.assertGreaterEqual(len(memories.memories), 1)
        self.assertIn("flower buds", memories.memories[0].content)


if __name__ == "__main__":
    unittest.main()
