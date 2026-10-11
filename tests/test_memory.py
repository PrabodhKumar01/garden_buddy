import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.memory import MemoryCreate, MemoryType
from app.services.backboard import BackboardService, backboard_service


class TestBackboardMemory(unittest.IsolatedAsyncioTestCase):
    """Test suite covering Phase 6 Backboard memory configuration, creation, and retrieval."""

    def setUp(self):
        self.client = TestClient(app)
        self.service = BackboardService()

    # 1. Connectivity Check
    async def test_connectivity_check_local_fallback(self):
        """When API key is not configured, connectivity check indicates local fallback."""
        self.service.api_key = None
        status = await self.service.check_connection()
        self.assertTrue(status["connected"])
        self.assertFalse(status["configured"])
        self.assertEqual(status["mode"], "local_fallback")

    @patch("httpx.AsyncClient.get")
    async def test_connectivity_check_cloud(self, mock_get):
        """When API key is configured, connectivity check contacts remote Backboard API."""
        self.service.api_key = "test-backboard-key"
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        status = await self.service.check_connection()
        self.assertTrue(status["connected"])
        self.assertTrue(status["configured"])
        self.assertEqual(status["mode"], "cloud")

    # 2. Memory Creation across meaningful categories
    async def test_create_meaningful_memories(self):
        """Verify creation of preferences, observations, history, and habits."""
        mem_pref = await self.service.create_memory(
            MemoryCreate(
                user_id=1,
                memory_type=MemoryType.PREFERENCE,
                content="Prefers organic pest control methods and morning gardening",
                importance=4,
            )
        )
        self.assertTrue(mem_pref.id.startswith("mem_"))
        self.assertEqual(mem_pref.memory_type, MemoryType.PREFERENCE)

        mem_obs = await self.service.create_memory(
            MemoryCreate(
                user_id=1,
                memory_type=MemoryType.OBSERVATION,
                content="Tomato developed yellow leaves on lower stems after heavy watering",
                importance=5,
                garden_id=1,
            )
        )
        self.assertEqual(mem_obs.memory_type, MemoryType.OBSERVATION)

        mem_habit = await self.service.create_memory(
            MemoryCreate(
                user_id=1,
                memory_type=MemoryType.HABIT,
                content="Usually gardens on weekend mornings between 8am and 10am",
                importance=3,
            )
        )
        self.assertEqual(mem_habit.memory_type, MemoryType.HABIT)

    # 3. Scoped Retrieval & User Isolation
    async def test_user_memory_isolation(self):
        """Memories of User A must not leak into User B's context."""
        await self.service.create_memory(
            MemoryCreate(
                user_id=10,
                memory_type=MemoryType.PREFERENCE,
                content="User 10 loves mint and cilantro",
            )
        )
        await self.service.create_memory(
            MemoryCreate(
                user_id=20,
                memory_type=MemoryType.PREFERENCE,
                content="User 20 only grows tomatoes and peppers",
            )
        )

        res_u10 = await self.service.retrieve_memories(user_id=10)
        self.assertEqual(res_u10.count, 1)
        self.assertIn("mint", res_u10.memories[0].content)

        res_u20 = await self.service.retrieve_memories(user_id=20)
        self.assertEqual(res_u20.count, 1)
        self.assertIn("tomatoes", res_u20.memories[0].content)

    # 4. Relevant Memory Filtering
    async def test_relevant_memory_filtering(self):
        """Querying for tomato should rank the tomato observation above unrelated memories."""
        await self.service.create_memory(
            MemoryCreate(
                user_id=30,
                memory_type=MemoryType.OBSERVATION,
                content="Tomato plant developed yellow leaves on lower branches",
                importance=4,
            )
        )
        await self.service.create_memory(
            MemoryCreate(
                user_id=30,
                memory_type=MemoryType.PREFERENCE,
                content="Prefers planting lavender near front porch",
                importance=3,
            )
        )

        res = await self.service.retrieve_memories(user_id=30, query="tomato watering leaves", limit=1)
        self.assertEqual(res.count, 1)
        self.assertIn("Tomato", res.memories[0].content)

    # 5. Formatted Prompt Context for Thinking Machines
    async def test_prompt_context_formatting(self):
        """Ensure context_text produces clean bulleted points for LLM reasoning."""
        await self.service.create_memory(
            MemoryCreate(
                user_id=40,
                memory_type=MemoryType.PREFERENCE,
                content="Avoid chemical fertilizers; prefers homemade compost.",
                importance=4,
            )
        )
        res = await self.service.retrieve_memories(user_id=40)
        self.assertIn("[AI PERSISTENT MEMORY CONTEXT]", res.context_text)
        self.assertIn("Preference", res.context_text)
        self.assertIn("chemical fertilizers", res.context_text)

    # 6. REST API Endpoints
    def test_api_memory_lifecycle(self):
        # Create
        create_res = self.client.post(
            "/api/v1/memories/",
            json={
                "user_id": 99,
                "memory_type": "observation",
                "content": "Coriander bolted quickly during 30°C hot week",
                "importance": 4
            }
        )
        self.assertEqual(create_res.status_code, 201)
        data = create_res.json()
        self.assertTrue(data["id"].startswith("mem_"))

        # Query
        query_res = self.client.get("/api/v1/memories/?user_id=99&query=coriander")
        self.assertEqual(query_res.status_code, 200)
        q_data = query_res.json()
        self.assertGreater(q_data["count"], 0)
        self.assertIn("Coriander", q_data["memories"][0]["content"])

        # Connectivity
        conn_res = self.client.get("/api/v1/memories/connectivity")
        self.assertEqual(conn_res.status_code, 200)
        self.assertIn("connected", conn_res.json())


if __name__ == "__main__":
    unittest.main()

