# 🌱 GardenBuddy — Backend (Render Deployment)

The GardenBuddy backend is built with **FastAPI**, **PostgreSQL**, and the AI agent stack (**Thinking Machines**, **Backboard.io**, **DevRelay MCP**, **Weather API**).

It deploys cleanly to **Render** as a Python Web Service with managed PostgreSQL.

---

## 🚀 How to Deploy to Render

### Method 1: Via Render Blueprint (`render.yaml` — Recommended)

1. Push your repository to **GitHub**.
2. Go to the [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** → **Blueprint**.
4. Connect your `garden-buddy` repository.
5. Render reads the root `render.yaml` and provisions:
   - **`gardenbuddy`**: FastAPI Web Service (Python runtime).
   - **`gardenbuddy-db`**: Managed PostgreSQL database.
6. Under Environment Variables for `gardenbuddy`, add your external API keys (with `sync: false`):
   - `WEATHER_API_KEY`
   - `BACKBOARD_API_KEY`
   - `THINKING_MACHINES_API_KEY`
7. Click **Apply**.

---

### Method 2: Via Manual Web Service

1. Create a PostgreSQL database on Render (`gardenbuddy-db`).
2. Create a **New Web Service**:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
3. Environment Variables:
   - `DATABASE_URL`: Your Render PostgreSQL Internal Connection String.
   - `ALLOWED_ORIGINS`: `*` (or your Vercel domain `https://your-frontend.vercel.app`).
   - `ENVIRONMENT`: `production`
   - `DEBUG`: `false`
   - `WEATHER_API_KEY`: `<your key>`
   - `BACKBOARD_API_KEY`: `<your key>`
   - `THINKING_MACHINES_API_KEY`: `<your key>`

---

## 🌐 Connecting with Vercel Frontend

The backend automatically enables CORS for all incoming requests by default (`ALLOWED_ORIGINS=*`).
You can restrict this to your specific Vercel frontend URL in production:

```bash
ALLOWED_ORIGINS="https://your-gardenbuddy.vercel.app,http://localhost:3000"
```

---

## 🧪 Local Verification

```bash
# Run local backend
uvicorn app.main:app --reload --port 8000

# Check health
curl http://127.0.0.1:8000/health

# View interactive API docs
http://127.0.0.1:8000/docs
```

