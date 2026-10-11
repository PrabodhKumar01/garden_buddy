# 🌱 GardenBuddy

### AI Garden Weather Agent

> **Use AI to spend less time on the screen and more time in the garden.**

GardenBuddy is an AI-powered gardening assistant built for the **Hacktoberfest 2026 — Touch Grass** theme.

Instead of being another chatbot that encourages users to stay online, GardenBuddy uses AI to determine what the user should do in their garden today.

---

# 🌿 The Idea

Traditional AI applications often work like:

```text
User
 ↓
Ask AI
 ↓
Read AI response
 ↓
Ask another question
 ↓
Stay on screen
```

GardenBuddy aims for:

```text
User
 ↓
Open GardenBuddy
 ↓
Get today's garden plan
 ↓
Close the app
 ↓
🌱 Go outside
 ↓
Garden
 ↓
Record observations
 ↓
AI remembers useful information
```

The AI is the assistant.

**The garden is the destination.**

---

# ✨ Features

## 🌱 Garden Management

Create a garden and record important information.

## 🌿 Plant Management

Add and manage plants in the garden.

## 🌦️ Weather-Aware Planning

GardenBuddy can access current and forecast weather information.

## 🧠 AI Reasoning

Thinking Machines helps reason about:

- Garden state
- Plants
- Weather
- Gardening knowledge
- User context

## 🧠 Persistent AI Memory

Backboard.io allows GardenBuddy to remember useful long-term context.

## 🔧 Agent Tools

DevRelay MCP provides tool access for the AI agent.

## 📚 Gardening Knowledge

RAG provides relevant gardening knowledge to the AI.

## ✅ Daily Garden Tasks

The AI generates practical activities for the user to perform outside.

---

# 🏗️ Architecture

```text
                       GardenBuddy
                            │
                         Frontend
                            │
                         FastAPI
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ↓             ↓             ↓
         PostgreSQL    Backboard.io      RAG
              │             │             │
              └─────────────┼─────────────┘
                            ↓
                    Thinking Machines
                       AI Reasoning
                            │
                            ↓
                      DevRelay MCP
                            │
                            ↓
                       Weather Tool
                            │
                            ↓
                       Weather API

                            ↓

                          Render
                        Deployment
```

---

# 🧩 Technology Stack

| Technology | Purpose |
|---|---|
| FastAPI | Backend API |
| PostgreSQL | Structured application data |
| Thinking Machines | AI reasoning |
| Backboard.io | Persistent AI memory |
| DevRelay MCP | Agent tool access |
| Weather API | Weather data |
| RAG | Gardening knowledge |
| Render | Deployment |

---

# 🔄 Example Workflow

Suppose the user's garden contains:

```text
🍅 Tomato
🌿 Coriander
🥬 Spinach
```

The user opens GardenBuddy.

The agent gathers relevant context:

```text
Garden state
+
Plant information
+
Weather
+
Gardening knowledge
+
Relevant memory
```

Thinking Machines reasons over that information.

The user receives:

```text
🌱 Today's Garden Plan

1. Check tomato soil moisture.
2. Inspect tomato leaves.
3. Harvest mature coriander.
4. Avoid unnecessary watering if rain is expected.
```

The user then goes outside and performs the tasks.

---

# 🧠 Why Multiple AI Components?

Each component has a specific responsibility.

### Thinking Machines

Handles reasoning.

```text
"What should this gardener do today?"
```

### Backboard.io

Handles persistent AI memory.

```text
"What should the AI remember about this gardener?"
```

### DevRelay MCP

Provides tools.

```text
"How can the agent access weather information?"
```

### RAG

Provides gardening knowledge.

```text
"What gardening information is relevant?"
```

These responsibilities should not be unnecessarily mixed.

---

# 🌦️ Weather Flow

Weather is retrieved through the tool workflow.

```text
Thinking Machines
       ↓
DevRelay MCP
       ↓
Weather Tool
       ↓
Weather API
       ↓
Weather Data
       ↓
Thinking Machines
```

The AI can therefore use real-world weather information when making its recommendation.

---

# 🧠 Memory Flow

GardenBuddy can remember useful information:

```text
User preference
       ↓
Backboard.io
       ↓
Future GardenBuddy interaction
       ↓
Relevant memory retrieved
       ↓
Personalized recommendation
```

The application should store only useful information.

---

# 📚 RAG Flow

Gardening knowledge is retrieved when required:

```text
Garden situation
       ↓
Knowledge retrieval
       ↓
Relevant gardening information
       ↓
Thinking Machines
       ↓
Recommendation
```

---

# 🔐 Security

GardenBuddy follows strict security principles.

The development agent must not:

- Search for credentials.
- Access SSH keys.
- Access unrelated personal files.
- Access password managers.
- Extract API keys.
- Upload unrelated user data.
- Perform destructive operations without approval.

See [`SECURITY.md`](SECURITY.md) for the complete policy.

---

# 📁 Project Documentation

The repository uses dedicated documentation files:

```text
PROJECT.md
```

Defines what GardenBuddy is and how its architecture works.

```text
AGENTS.md
```

Defines how the AI coding agent should behave.

```text
TASKS.md
```

Defines the development roadmap.

```text
SECURITY.md
```

Defines security boundaries.

---

# 🚀 Quickstart & Setup

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/<your-username>/gardenbuddy.git
cd gardenbuddy

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example configuration:
```bash
cp .env.example .env
```
*(Optionally provide external API keys; if left blank, GardenBuddy seamlessly activates built-in resilient local fallbacks).*

### 3. Run Application Locally

```bash
uvicorn app.main:app --reload
```

- **Interactive Dashboard:** [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

# ⚙️ Configuration & Environment Variables

| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | Runtime environment (`development` / `production`) | `development` |
| `DEBUG` | Enable debug logs and auto-reload | `True` |
| `PORT` | Application server port | `8000` |
| `DATABASE_URL` | PostgreSQL or SQLite connection string | `sqlite:///./gardenbuddy.db` |
| `ALLOWED_ORIGINS` | Allowed CORS origins (comma-separated or JSON) | `*` |
| `WEATHER_API_KEY` | Weather service API key | *(Optional, fallback active)* |
| `BACKBOARD_API_KEY` | Backboard.io persistent memory key | *(Optional, fallback active)* |
| `THINKING_MACHINES_API_KEY` | Thinking Machines AI reasoning key | *(Optional, fallback active)* |
| `DEVRELAY_GATEWAY_URL` | DevRelay MCP Gateway URL | `http://localhost:8080` |

---

# 📡 Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Application health and database telemetry |
| `GET` | `/dashboard` | Interactive frontend web UI |
| `POST` | `/api/v1/gardens/` | Create a garden |
| `GET` | `/api/v1/gardens/` | List gardens |
| `POST` | `/api/v1/plants/` | Add a plant to a garden |
| `GET` | `/api/v1/tasks/today` | Retrieve today's daily gardening tasks |
| `POST` | `/api/v1/tasks/{id}/complete` | Mark task completed and record observations |
| `POST` | `/api/v1/agent/daily-workflow` | Trigger end-to-end AI agent daily garden plan |
| `POST` | `/api/v1/mcp/execute` | DevRelay MCP tool invocation |

---

# ☁️ Deployment Guide

GardenBuddy is structured so you can deploy as a unified monolith or decouple into **Vercel (Frontend)** and **Render (Backend)**:

### 🌐 Deploy Frontend to Vercel
The [`frontend/`](frontend/) directory is a standalone web app ready for Vercel Edge:
1. Push to GitHub and go to [vercel.com](https://vercel.com).
2. Create **New Project**, select your repository.
3. Set **Root Directory** to `frontend`.
4. Framework Preset: `Other` (static).
5. Deploy!
6. In the app header or in [`frontend/config.js`](frontend/config.js), point the API endpoint to your Render backend URL.

### 🚀 Deploy Backend to Render
The backend FastAPI application deploys automatically with managed PostgreSQL:
1. In [Render Dashboard](https://dashboard.render.com), click **New +** $\rightarrow$ **Blueprint**.
2. Select your GitHub repository.
3. Render reads [`render.yaml`](render.yaml) and provisions:
   - A managed **PostgreSQL** database (`gardenbuddy-db`)
   - A **FastAPI Web Service** (`gardenbuddy`) running `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Access your live API docs at `https://<your-service>.onrender.com/docs` and health check at `/health`.

---

# 🚀 Development Workflow

---

# 🌱 Hacktoberfest 2026 — Touch Grass

GardenBuddy is designed around the theme:

> **Build something with open-weight models or open-source AI that gets people off the screen and into the world.**

GardenBuddy applies this idea directly.

The AI performs the digital work:

```text
Understand
Reason
Plan
```

The user performs the real-world work:

```text
Go outside
Garden
Observe
Act
```

The goal is simple:

> **The screen should be the shortest part of the experience.**

---

# 🎯 MVP

The initial MVP aims to support:

- Garden creation
- Plant management
- Weather retrieval
- Gardening knowledge retrieval
- AI reasoning
- Persistent AI memory
- Daily garden plans
- Garden task completion

Advanced features should come only after the MVP is stable.

---

# 🛣️ Future Ideas

Possible future features include:

- Plant Doctor
- Garden Journal
- Plant image analysis
- Garden history
- Harvest tracking
- More advanced weather planning

These are not required for the initial MVP.

---

# 🤝 Contribution

Contributions should respect:

- `PROJECT.md`
- `AGENTS.md`
- `TASKS.md`
- `SECURITY.md`

Changes should have a clear purpose and should not introduce unnecessary technologies.

---

# 📜 License

Add the project's chosen open-source license here once the license has been selected.