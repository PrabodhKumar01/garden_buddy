import unittest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app as fastapi_app


class TestGardenBuddyAPI(unittest.TestCase):
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

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        fastapi_app.dependency_overrides.clear()

    def test_root_and_health(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("GardenBuddy API", res.json()["message"])

        res_h = self.client.get("/health")
        self.assertEqual(res_h.status_code, 200)
        self.assertEqual(res_h.json()["status"], "healthy")

    def test_phase_3_1_garden_crud(self):
        # 1. Create User
        u_res = self.client.post("/api/v1/users/", json={"username": "alice", "email": "alice@garden.com"})
        self.assertEqual(u_res.status_code, 201)
        user_id = u_res.json()["id"]

        # 2. Create Garden
        g_payload = {
            "user_id": user_id,
            "name": "Sunny Balcony Garden",
            "location": "San Francisco",
            "garden_type": "Balcony",
            "sunlight": "Full Sun",
            "notes": "Pots on the south-facing balcony"
        }
        g_res = self.client.post("/api/v1/gardens/", json=g_payload)
        self.assertEqual(g_res.status_code, 201)
        garden_id = g_res.json()["id"]

        # 3. Read Garden
        get_res = self.client.get(f"/api/v1/gardens/{garden_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["name"], "Sunny Balcony Garden")

        # 4. List Gardens
        list_res = self.client.get(f"/api/v1/gardens/?user_id={user_id}")
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(len(list_res.json()), 1)

        # 5. Update Garden
        up_res = self.client.put(f"/api/v1/gardens/{garden_id}", json={"name": "Sunny Rooftop Garden"})
        self.assertEqual(up_res.status_code, 200)
        self.assertEqual(up_res.json()["name"], "Sunny Rooftop Garden")

        # 6. Delete Garden
        del_res = self.client.delete(f"/api/v1/gardens/{garden_id}")
        self.assertEqual(del_res.status_code, 204)

        # 7. Confirm 404
        self.assertEqual(self.client.get(f"/api/v1/gardens/{garden_id}").status_code, 404)

    def test_phase_3_2_plant_crud(self):
        # Setup user and garden
        u_res = self.client.post("/api/v1/users/", json={"username": "bob"})
        user_id = u_res.json()["id"]
        g_res = self.client.post("/api/v1/gardens/", json={"user_id": user_id, "name": "Veggie Bed"})
        garden_id = g_res.json()["id"]

        # 1. Add Plant
        p_payload = {
            "garden_id": garden_id,
            "name": "Roma Tomato",
            "species": "Solanum lycopersicum",
            "date_planted": "2026-04-15",
            "location_in_garden": "Bed 1",
            "notes": "Healthy seedling"
        }
        p_res = self.client.post("/api/v1/plants/", json=p_payload)
        self.assertEqual(p_res.status_code, 201)
        plant_id = p_res.json()["id"]

        # 2. Retrieve Plants
        list_res = self.client.get(f"/api/v1/plants/?garden_id={garden_id}")
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(len(list_res.json()), 1)

        # 3. Get Plant by ID
        get_res = self.client.get(f"/api/v1/plants/{plant_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["species"], "Solanum lycopersicum")

        # 4. Update Plant
        up_res = self.client.put(f"/api/v1/plants/{plant_id}", json={"notes": "Flowering stage reached"})
        self.assertEqual(up_res.status_code, 200)
        self.assertEqual(up_res.json()["notes"], "Flowering stage reached")

        # 5. Remove Plant
        del_res = self.client.delete(f"/api/v1/plants/{plant_id}")
        self.assertEqual(del_res.status_code, 204)
        self.assertEqual(self.client.get(f"/api/v1/plants/{plant_id}").status_code, 404)

    def test_phase_3_3_task_apis(self):
        # Setup
        u_res = self.client.post("/api/v1/users/", json={"username": "charlie"})
        user_id = u_res.json()["id"]
        g_res = self.client.post("/api/v1/gardens/", json={"user_id": user_id, "name": "Herb Garden"})
        garden_id = g_res.json()["id"]
        p_res = self.client.post("/api/v1/plants/", json={"garden_id": garden_id, "name": "Coriander"})
        plant_id = p_res.json()["id"]

        today_str = date.today().isoformat()

        # 1. Create Tasks
        t_payload = {
            "garden_id": garden_id,
            "plant_id": plant_id,
            "title": "Harvest mature coriander leaves",
            "description": "Trim gently",
            "category": "harvest",
            "task_date": today_str,
            "source": "ai_generated"
        }
        t_res = self.client.post("/api/v1/tasks/", json=t_payload)
        self.assertEqual(t_res.status_code, 201)
        task_id = t_res.json()["id"]
        self.assertFalse(t_res.json()["is_completed"])

        # 2. Retrieve Today's Tasks
        today_res = self.client.get(f"/api/v1/tasks/today?garden_id={garden_id}")
        self.assertEqual(today_res.status_code, 200)
        tasks = today_res.json()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["title"], "Harvest mature coriander leaves")

        # 3. Mark Task Complete & Record Relevant Result
        c_res = self.client.patch(
            f"/api/v1/tasks/{task_id}/complete",
            json={
                "is_completed": True,
                "result_notes": "Harvested fresh bunch, plant is thriving."
            }
        )
        self.assertEqual(c_res.status_code, 200)
        completed_task = c_res.json()
        self.assertTrue(completed_task["is_completed"])
        self.assertIsNotNone(completed_task["completed_at"])
        self.assertEqual(completed_task["result_notes"], "Harvested fresh bunch, plant is thriving.")

        # 4. List Tasks with filter
        list_res = self.client.get(f"/api/v1/tasks/?garden_id={garden_id}&is_completed=true")
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(len(list_res.json()), 1)

        # 5. Delete Task
        del_res = self.client.delete(f"/api/v1/tasks/{task_id}")
        self.assertEqual(del_res.status_code, 204)
        self.assertEqual(self.client.get(f"/api/v1/tasks/{task_id}").status_code, 404)


if __name__ == "__main__":
    unittest.main()

