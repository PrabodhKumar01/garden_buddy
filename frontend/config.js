// GardenBuddy Frontend Configuration
// Configures the backend API URL for local development and production deployments.

(function () {
  // Default production backend URL on Render.
  // Update this to your deployed Render URL (e.g. "https://gardenbuddy.onrender.com")
  const DEFAULT_PROD_BACKEND_URL = " https://garden-buddy-pn9h.onrender.com";

  function resolveApiBaseUrl() {
    // 1. Check window-level override (injected by host or test)
    if (window.GARDENBUDDY_API_URL) {
      return window.GARDENBUDDY_API_URL.replace(/\/+$/, "");
    }

    // 2. Check localStorage for user-configured custom backend URL
    const stored = localStorage.getItem("gardenbuddy_api_url");
    if (stored && stored.trim() !== "") {
      return stored.trim().replace(/\/+$/, "");
    }

    // 3. Local development
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") {
      // If served directly by FastAPI on port 8000, use relative paths
      if (window.location.port === "8000") {
        return "";
      }
      // If served by Vercel CLI / Live Server / dev server (e.g. port 3000 or 5500), point to local FastAPI
      return "http://127.0.0.1:8000";
    }

    // 4. Deployed on Vercel: default to Render backend
    return DEFAULT_PROD_BACKEND_URL;
  }

  window.API_BASE_URL = resolveApiBaseUrl();

  // Helper function to update backend API URL at runtime from the browser UI
  window.setGardenBuddyApiUrl = function (newUrl) {
    if (!newUrl || newUrl.trim() === "") {
      localStorage.removeItem("gardenbuddy_api_url");
    } else {
      let cleaned = newUrl.trim().replace(/\/+$/, "");
      if (!cleaned.startsWith("http://") && !cleaned.startsWith("https://")) {
        cleaned = "https://" + cleaned;
      }
      localStorage.setItem("gardenbuddy_api_url", cleaned);
    }
    window.location.reload();
  };
})();

