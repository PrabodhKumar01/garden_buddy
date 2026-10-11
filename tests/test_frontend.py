import unittest
from fastapi.testclient import TestClient

from app.main import app


class TestFrontendDashboard(unittest.TestCase):
    """Test suite for Phase 10 Frontend Dashboard and assets."""

    def setUp(self):
        self.client = TestClient(app)

    def test_dashboard_endpoint(self):
        """Verify the /dashboard endpoint serves the HTML page."""
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers["content-type"])
        html = res.text
        self.assertIn("GardenBuddy", html)
        self.assertIn("Today's Daily Garden Plan", html)
        self.assertIn("Plants in Garden", html)
        self.assertIn("Touch Grass", html)

    def test_static_assets(self):
        """Verify CSS and JavaScript assets are accessible."""
        css_res = self.client.get("/static/styles.css")
        self.assertEqual(css_res.status_code, 200)
        self.assertIn("text/css", css_res.headers["content-type"])
        self.assertIn("--primary", css_res.text)

        js_res = self.client.get("/static/app.js")
        self.assertEqual(js_res.status_code, 200)
        self.assertIn("javascript", js_res.headers["content-type"])
        self.assertIn("loadGardenData", js_res.text)

    def test_root_points_to_dashboard(self):
        """Verify root endpoint points users and agents to /dashboard."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["dashboard"], "/dashboard")


if __name__ == "__main__":
    unittest.main()

