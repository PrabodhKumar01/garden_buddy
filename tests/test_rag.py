import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.services.rag import RAGService, rag_service


class TestRAGKnowledgeRetrieval(unittest.TestCase):
    """Test suite for Phase 5 Gardening Knowledge / RAG."""

    def setUp(self):
        self.client = TestClient(app)
        self.rag = RAGService()

    # 1. Verify relevant knowledge is retrieved
    def test_relevant_knowledge_retrieved_for_plant_problem(self):
        """Querying for yellow leaves on tomato returns the tomato yellow leaves knowledge."""
        response = self.rag.retrieve(
            query="my tomato leaves are turning yellow what should I do",
            plant_names=["tomato"],
            limit=3
        )
        self.assertGreater(response.count, 0)
        top_snippet = response.results[0]
        self.assertEqual(top_snippet.id, "tomato_yellow_leaves")
        self.assertEqual(top_snippet.plant, "tomato")
        self.assertIn("overwatering", top_snippet.content.lower())

    def test_relevant_knowledge_retrieved_for_rain_situation(self):
        """Querying for rain and watering retrieves rain-specific watering guidance."""
        response = self.rag.retrieve(
            query="rain expected tomorrow should I water my garden",
            limit=2
        )
        self.assertGreater(response.count, 0)
        snippet_ids = [s.id for s in response.results]
        # Should retrieve rain watering rules
        self.assertTrue(
            "general_weather_rain_watering" in snippet_ids or "tomato_watering" in snippet_ids
        )

    # 2. Verify irrelevant knowledge is minimized
    def test_irrelevant_knowledge_minimized(self):
        """Querying specifically for coriander care does not return tomato or spinach articles."""
        response = self.rag.retrieve(
            query="how to harvest coriander leaves before bolting",
            plant_names=["coriander"],
            limit=2
        )
        self.assertGreater(response.count, 0)
        for snippet in response.results:
            # Irrelevant plants like spinach should not be in the top results for coriander
            self.assertNotEqual(snippet.plant, "spinach")
        # Ensure count adheres to limit
        self.assertLessEqual(response.count, 2)

    # 3. Handle no-result situations gracefully
    def test_no_result_graceful_handling(self):
        """Completely unrelated queries return 0 results and polite fallback context."""
        response = self.rag.retrieve(
            query="quantum computer cryptocurrency blockchain algorithm",
            limit=3
        )
        self.assertEqual(response.count, 0)
        self.assertEqual(len(response.results), 0)
        self.assertIn("No specific gardening knowledge found", response.context_text)

    # 4. Verify context text reaches AI reasoning layer format
    def test_context_text_structure(self):
        """Ensure context_text is formatted cleanly for prompt injection."""
        response = self.rag.retrieve(
            query="mint in garden container",
            plant_names=["mint"],
            limit=2
        )
        self.assertIn("[GARDENING KNOWLEDGE BASE CONTEXT]", response.context_text)
        self.assertIn("Mint", response.context_text)
        self.assertIn("container", response.context_text.lower())

    # 5. API Endpoint integration tests
    def test_api_retrieve_endpoint(self):
        payload = {
            "query": "spinach planting in cool weather",
            "plant_names": ["spinach"],
            "limit": 2
        }
        res = self.client.post("/api/v1/knowledge/retrieve", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["query"], payload["query"])
        self.assertGreater(data["count"], 0)
        self.assertEqual(data["results"][0]["plant"], "spinach")

    def test_api_search_get_endpoint(self):
        res = self.client.get("/api/v1/knowledge/search?query=finger+soil+test&limit=1")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["count"], 0)
        self.assertEqual(data["results"][0]["id"], "general_soil_moisture_finger_test")


if __name__ == "__main__":
    unittest.main()

