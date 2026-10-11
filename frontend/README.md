# 🌱 GardenBuddy — Frontend (Vercel Deployment)

This directory contains the standalone web frontend for GardenBuddy, built to deploy to **Vercel** with zero build configuration.

---

## 🚀 How to Deploy to Vercel

### Method 1: Via Vercel Web Dashboard (Recommended)

1. Push your repository to **GitHub**.
2. Go to [vercel.com](https://vercel.com) and log in.
3. Click **Add New...** → **Project**.
4. Import your `garden-buddy` repository.
5. In the **Configure Project** screen:
   - Expand **Root Directory**: Click **Edit** and select `frontend`.
   - **Framework Preset**: Select `Other` (Static HTML/JS).
   - **Build and Output Settings**: Leave defaults (no build command needed).
6. Click **Deploy**.

Your frontend will be live at `https://<your-project>.vercel.app`!

---

### Method 2: Via Vercel CLI

```bash
cd frontend
npx vercel
```

Follow the prompts:
- Link to existing project? `No`
- Project name: `gardenbuddy-frontend`
- Directory: `.`
- Override settings? `No`

---

## 🔗 Connecting to the Render Backend

The frontend communicates with your FastAPI backend deployed on **Render** (or any public URL):

1. By default, `config.js` connects to `https://gardenbuddy.onrender.com`.
2. To point to your specific Render service:
   - **Option A (In-Browser)**: Click the **🔗 API** badge in the top navigation bar of the web app, enter your Render URL (e.g. `https://my-gardenbuddy-api.onrender.com`), and click **Save & Reload**.
   - **Option B (Code)**: Update `DEFAULT_PROD_BACKEND_URL` in `config.js`.

---

## 💻 Local Development

Run locally using any static web server:

```bash
cd frontend
npx serve .
# Or open index.html with Live Server in VS Code
```

When accessed on `localhost`, the frontend automatically calls `http://127.0.0.1:8000` (your local FastAPI server).

