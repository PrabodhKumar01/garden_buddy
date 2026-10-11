import unittest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.crud.crud_plant import plant_crud
from app.crud.crud_task import task_crud
from app.main import app as fastapi_app
from app.models.garden import Garden
from app.models.plant import Plant
from app.models.user import User
from app.schemas.memory import MemoryType
from app.schemas.task import TaskCreate, TaskStatusUpdate
from app.services.backboard import backboard_service
from app.services.task_completion import task_completion_service


class TestTaskCompletionWorkflow(unittest.IsolatedAsyncioTestCase):
    """Test suite for Phase 11: Task completion, observations, garden state, and Backboard memory."""

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

        # Seed user, garden, plants
        self.user = User(username="gardener_sam", email="sam@example.com")
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)

        self.garden = Garden(
            user_id=self.user.id,
            name="Community Plot",
            location="Denver",
            garden_type="Raised Bed"
        )
        self.db.add(self.garden)
        self.db.commit()
        self.db.refresh(self.garden)

        self.plant = Plant(
            garden_id=self.garden.id,
            name="San Marzano Tomato",
            species="Solanum lycopersicum",
            notes="Young transplant"
        )
        self.db.add(self.plant)
        self.db.commit()
        self.db.refresh(self.plant)

    def tearDown(self):
        self.db.query(Plant).delete()
        self.db.query(Garden).delete()
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()

    # 1. Basic Task Completion without notes
    async def test_task_completion_basic(self):
        task = task_crud.create(
            db=self.db,
            task_in=TaskCreate(
                garden_id=self.garden.id,
                plant_id=self.plant.id,
                title="Weed around bed borders",
                category="maintenance",
                task_date=date.today(),
                is_completed=False
            )
        )
        self.assertFalse(task.is_completed)
        self.assertIsNone(task.completed_at)

        completed = await task_completion_service.complete_task(
            db=self.db,
            task_id=task.id,
            status_in=TaskStatusUpdate(is_completed=True)
        )
        self.assertIsNotNone(completed)
        self.assertTrue(completed.is_completed)
        self.assertIsNotNone(completed.completed_at)

    # 2. Observation recording updates Plant State and Backboard Memory
    async def test_task_completion_records_observation_and_updates_plant_notes(self):
        task = task_crud.create(
            db=self.db,
            task_in=TaskCreate(
                garden_id=self.garden.id,
                plant_id=self.plant.id,
                title="Inspect tomato foliage",
                category="inspection",
                task_date=date.today(),
                is_completed=False
            )
        )

        obs_note = "First blossom clusters appeared, lower leaves look healthy and green."
        completed = await task_completion_service.complete_task(
            db=self.db,
            task_id=task.id,
            status_in=TaskStatusUpdate(is_completed=True, result_notes=obs_note)
        )

        self.assertEqual(completed.result_notes, obs_note)

        # Check plant state updated
        refreshed_plant = plant_crud.get(db=self.db, plant_id=self.plant.id)
        self.assertIn(obs_note, refreshed_plant.notes)

        # Check Backboard memory recorded
        resp = await backboard_service.retrieve_memories(
            user_id=self.user.id,
            garden_id=self.garden.id,
            query="blossom"
        )
        self.assertEqual(len(resp.memories), 1)
        self.assertIn("San Marzano Tomato", resp.memories[0].content)
        self.assertIn(obs_note, resp.memories[0].content)

    # 3. Watering Task records Garden History in Backboard
    async def test_watering_task_creates_history_memory(self):
        task = task_crud.create(
            db=self.db,
            task_in=TaskCreate(
                garden_id=self.garden.id,
                plant_id=self.plant.id,
                title="Deep soak tomato root zone",
                category="watering",
                task_date=date.today(),
                is_completed=False
            )
        )

        await task_completion_service.complete_task(
            db=self.db,
            task_id=task.id,
            status_in=TaskStatusUpdate(is_completed=True)
        )

        resp = await backboard_service.retrieve_memories(
            user_id=self.user.id,
            garden_id=self.garden.id,
            query="Watered"
        )
        self.assertEqual(len(resp.memories), 1)
        self.assertIn("Watered San Marzano Tomato", resp.memories[0].content)

    # 4. Harvest Task records Garden History in Backboard
    async def test_harvest_task_creates_history_memory(self):
        task = task_crud.create(
            db=self.db,
            task_in=TaskCreate(
                garden_id=self.garden.id,
                plant_id=self.plant.id,
                title="Harvest ripe tomatoes",
                category="harvest",
                task_date=date.today(),
                is_completed=False
            )
        )

        await task_completion_service.complete_task(
            db=self.db,
            task_id=task.id,
            status_in=TaskStatusUpdate(is_completed=True)
        )

        resp = await backboard_service.retrieve_memories(
            user_id=self.user.id,
            garden_id=self.garden.id,
            query="Harvested"
        )
        self.assertEqual(len(resp.memories), 1)
        self.assertIn("Harvested San Marzano Tomato", resp.memories[0].content)

    # 5. Unchecking task removes completed timestamp
    async def test_task_uncomplete(self):
        task = task_crud.create(
            db=self.db,
            task_in=TaskCreate(
                garden_id=self.garden.id,
                plant_id=self.plant.id,
                title="Prune suckers",
                category="care",
                task_date=date.today(),
                is_completed=True
            )
        )
        self.assertTrue(task.is_completed)

        uncompleted = await task_completion_service.complete_task(
            db=self.db,
            task_id=task.id,
            status_in=TaskStatusUpdate(is_completed=False)
        )
        self.assertFalse(uncompleted.is_completed)
        self.assertIsNone(uncompleted.completed_at)

    # 6. API Endpoint PATCH /api/v1/tasks/{task_id}/complete
    def test_api_task_complete_endpoint(self):
        task = task_crud.create(
            db=self.db,
            task_in=TaskCreate(
                garden_id=self.garden.id,
                plant_id=self.plant.id,
                title="Inspect soil dampness",
                category="inspection",
                task_date=date.today(),
                is_completed=False
            )
        )

        res = self.client.patch(
            f"/api/v1/tasks/{task.id}/complete",
            json={
                "is_completed": True,
                "result_notes": "Topsoil dry, 2 inches deep is damp."
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_completed"])
        self.assertEqual(data["result_notes"], "Topsoil dry, 2 inches deep is damp.")

        # Test non-existent task 404
        bad_res = self.client.patch(
            "/api/v1/tasks/99999/complete",
            json={"is_completed": True}
        )
        self.assertEqual(bad_res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
