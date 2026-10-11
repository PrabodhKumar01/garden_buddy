# 🌱 GardenBuddy — AI Garden Weather Agent

## 1. Project Overview

**GardenBuddy** is an AI-powered gardening assistant designed to help users decide **what they should do in their garden today**.

Instead of requiring the user to continuously ask questions, GardenBuddy combines:

- Garden and plant information
- Current and forecast weather
- Gardening knowledge
- User history and preferences
- AI reasoning

to generate a personalized **Daily Garden Plan**.

The project follows the Hacktoberfest 2026 **"Touch Grass"** theme by using AI to encourage users to perform real-world gardening activities rather than keeping them on the screen.

### Example

A user opens GardenBuddy and receives:

> 🌱 **Today's Garden Plan**
>
> 🌧️ Rain is expected tomorrow.
>
> 💧 Don't water your tomatoes today.
>
> 🌿 Harvest mature coriander.
>
> 🍅 Check the tomato leaves for yellowing.
>
> 🌱 Consider planting spinach this week.

The user then goes outside, performs the recommended activities, and records the results.

---

# 2. Project Goal

The main goal is to build an AI garden agent that can:

1. Understand the user's garden.
2. Remember relevant gardening information.
3. Access weather information when necessary.
4. Reason about the garden and weather together.
5. Generate useful daily gardening tasks.
6. Encourage the user to spend time actually gardening.

The screen should be the shortest part of the experience.

---

# 3. Core Technologies

The project will use the following technologies:

| Technology | Responsibility |
|---|---|
| **FastAPI** | Backend API |
| **PostgreSQL** | Persistent application data |
| **Thinking Machines** | AI reasoning and agent intelligence |
| **Backboard.io** | Persistent AI memory |
| **DevRelay MCP** | Tool access for the AI agent |
| **Weather API** | Weather and forecast data |
| **Render** | Application deployment |
| **RAG** | Retrieval of relevant gardening knowledge |

Optional technologies such as Redis may be introduced later only if a concrete requirement appears.

---

# 4. High-Level Architecture

```text
                         🌱 GardenBuddy
                              │
                              ↓
                         Frontend
                              │
                              ↓
                           FastAPI
                              │
                 ┌────────────┼────────────┐
                 │            │            │
                 ↓            ↓            ↓
            PostgreSQL    Backboard.io    RAG
                 │            │            │
                 │            │            │
                 └────────────┼────────────┘
                              ↓
                       Thinking Machines
                         AI Reasoning
                              │
                              ↓
                        DevRelay MCP
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ↓                         ↓
          Weather Tool               Other Tools
                 │
                 ↓
             Weather API
                             
                              ↓
                           Render
                         Deployment
```

---

# 5. Architectural Responsibilities

Each technology must have a clear responsibility.

## 5.1 FastAPI

FastAPI is the main backend framework.

It will:

- Expose API endpoints.
- Receive requests from the frontend.
- Validate request data.
- Communicate with PostgreSQL.
- Communicate with the AI layer.
- Manage authentication if authentication is added.
- Coordinate application logic.

FastAPI should remain the main application backend rather than putting business logic directly into the frontend.

---

# 6. PostgreSQL

PostgreSQL will store the application's structured data.

Possible entities include:

```text
users
gardens
plants
plant_actions
garden_tasks
weather_records
```

Example:

```text
User
 └── Garden
      ├── Tomato
      ├── Coriander
      └── Spinach
```

PostgreSQL is responsible for **application state and structured information**.

It is not the primary AI memory system.

---

# 7. Backboard.io

Backboard.io will provide persistent memory for the AI agent.

The purpose is to allow GardenBuddy to remember information that is useful for future interactions.

Examples:

```text
User prefers low-maintenance plants.

User planted tomatoes recently.

The user's tomato previously developed yellow leaves.

User usually gardens in the morning.

User prefers organic gardening methods.
```

This allows the AI to provide personalized recommendations instead of treating every interaction as a new conversation.

### PostgreSQL vs Backboard

The distinction should remain clear:

```text
PostgreSQL
    ↓
Application data
    ↓
Structured and queryable records


Backboard.io
    ↓
AI memory
    ↓
Context useful for future AI interactions
```

---

# 8. Thinking Machines

Thinking Machines will be responsible for the AI reasoning layer.

The AI should not simply generate generic gardening advice.

It should reason using multiple sources of context:

```text
Garden state
      +
Plant information
      +
Weather
      +
Gardening knowledge
      +
User memory
      ↓
AI reasoning
      ↓
Today's Garden Plan
```

For example:

```text
Tomatoes need watering
        +
Rain expected tomorrow
        +
User watered yesterday
        ↓
AI reasoning
        ↓
Do not recommend watering today.
```

The purpose of the AI layer is to make the final decision based on available information.

---

# 9. DevRelay MCP

DevRelay MCP will provide the agent with access to external tools.

MCP should be treated as the **tool-access layer**, not as the weather provider itself.

For example:

```text
Thinking Machines
       ↓
   MCP request
       ↓
DevRelay MCP
       ↓
Weather tool
       ↓
Weather API
       ↓
Weather data
```

The agent can therefore request information when it needs it.

Example:

```text
Agent:
"I need tomorrow's weather before deciding whether
the user should water the tomatoes."

        ↓

DevRelay MCP

        ↓

Weather tool

        ↓

Weather API

        ↓

Rain probability = high

        ↓

Agent:
"Do not recommend watering today."
```

This makes weather access part of the agent's tool-use workflow rather than hard-coding every decision into the backend.

---

# 10. Weather API

The Weather API will provide real-world weather information.

Potential data includes:

- Temperature
- Rain probability
- Rain forecast
- Humidity
- Weather conditions
- Forecast for upcoming days

The Weather API is the actual source of weather data.

MCP provides the interface through which the AI agent can access the weather capability.

```text
Weather API
     ↑
     │
Weather Tool
     ↑
     │
DevRelay MCP
     ↑
     │
Thinking Machines
```

---

# 11. RAG

RAG will be used to retrieve relevant gardening knowledge when the AI needs additional information.

The knowledge base can contain information such as:

```text
Plant requirements
Watering guidelines
Soil requirements
Sunlight requirements
Planting information
Common plant problems
Seasonal gardening information
Pest information
```

The basic flow is:

```text
User's garden
      ↓
Current situation
      ↓
Retrieve relevant gardening knowledge
      ↓
RAG context
      ↓
Thinking Machines
      ↓
Recommendation
```

RAG should provide **knowledge**, while PostgreSQL and Backboard provide information about the **specific user and their garden**.

---

# 12. Render

Render will be used to deploy the application.

The deployment may contain:

```text
Frontend
Backend / FastAPI
Supporting services
```

Render is an infrastructure/deployment component.

It does not perform the AI reasoning itself.

---

# 13. Daily Garden Agent Workflow

The central workflow of GardenBuddy is:

```text
User opens GardenBuddy
        ↓
Identify user's garden
        ↓
Retrieve garden information
        ↓
Retrieve relevant AI memory
        ↓
Determine whether current weather is needed
        ↓
Thinking Machines requests weather through MCP
        ↓
DevRelay MCP
        ↓
Weather API
        ↓
Retrieve relevant gardening knowledge through RAG
        ↓
Thinking Machines reasons over the information
        ↓
Generate Today's Garden Plan
        ↓
User goes outside
        ↓
User performs gardening tasks
        ↓
User records observations/results
        ↓
Update application data and AI memory
```

---

# 14. Example Agent Decision

### Input

```text
Plant:
Tomato

Last watered:
Yesterday

Forecast:
Heavy rain tomorrow

Soil:
Unknown

User preference:
Morning gardening
```

### Agent reasoning

The agent considers:

```text
Last watering
+
Upcoming rainfall
+
Plant requirements
+
User preference
```

### Output

```text
🌱 Today's Garden Plan

1. Do not water the tomato yet.
2. Check the soil moisture this morning.
3. Inspect the leaves for yellowing.
4. Remove damaged leaves if necessary.
5. Prepare the garden for tomorrow's rain.
```

The important point is that the AI recommendation is based on the available context rather than being a static predefined response.

---

# 15. MVP Features

The first version should remain small.

## Feature 1 — Garden Creation

User can create a garden.

Information may include:

```text
Garden name
Location
Garden type
Sunlight
```

---

## Feature 2 — Add Plants

User can add plants.

Example:

```text
Tomato
Coriander
Spinach
Mint
```

Each plant can have information such as:

```text
Plant name
Date planted
Location in garden
Notes
```

---

## Feature 3 — Weather Retrieval

GardenBuddy can retrieve current/forecast weather through the MCP tool.

---

## Feature 4 — AI Daily Plan

The agent generates:

```text
Today's weather
+
Garden state
+
Plant information
+
Relevant knowledge
+
User memory
        ↓
Daily Garden Plan
```

---

## Feature 5 — Complete Garden Tasks

The user can mark tasks as completed.

Example:

```text
☑ Check soil
☑ Inspect tomato leaves
☐ Harvest coriander
☐ Water plants
```

---

## Feature 6 — Garden Memory

Important user/garden information can be remembered through Backboard.io.

---

# 16. Future Features

These should not be required for the MVP.

Possible future improvements:

### Plant Doctor

Allow the user to upload a plant photograph and receive assistance identifying possible problems.

### Garden Journal

Allow users to record:

```text
Photos
Observations
Plant growth
Problems
Harvests
```

### Personalized Garden History

Show:

```text
Plants grown
Tasks completed
Harvest history
Garden activity
```

### Smarter Weather Planning

Generate multi-day garden plans using weather forecasts.

---

# 17. What We Are NOT Building

To keep the project focused, GardenBuddy will not initially include:

- Complex microservices
- Multiple databases
- Kubernetes
- Unnecessary background infrastructure
- A large social network
- A generic AI chatbot
- Excessive gamification
- Unrelated AI features

Every technology must have a clear purpose.

---

# 18. Core Design Principle

GardenBuddy should follow one central principle:

> **Use AI to get the user outside, not to keep the user talking to AI.**

The ideal interaction is:

```text
Open app
    ↓
Get today's plan
    ↓
Close app
    ↓
🌱 Go garden
    ↓
Complete tasks
    ↓
Return and record results
```

The application should therefore minimize unnecessary screen time.

---

# 19. Hacktoberfest "Touch Grass" Alignment

GardenBuddy directly addresses the theme by connecting AI assistance to a real-world activity.

The AI does the planning and reasoning.

The user does the gardening.

```text
AI
 ↓
Plan
 ↓
Real-world action
 ↓
🌱 Gardening
 ↓
Observation
 ↓
AI memory
 ↓
Next plan
```

The project therefore uses AI as a bridge between the digital and physical world rather than as a destination.

---

# 20. Initial Technology Stack

The initial implementation will use:

```text
Frontend
    ↓
FastAPI
    ↓
PostgreSQL
    ↓
Thinking Machines
    ↓
Backboard.io
    ↓
DevRelay MCP
    ↓
Weather API
    ↓
RAG
    ↓
Render
```

Technologies should only be added or replaced when a concrete project requirement justifies the change.

---

# 21. Development Priority

Implementation should proceed in this order:

```text
1. Project setup
       ↓
2. PostgreSQL database
       ↓
3. Garden & plant APIs
       ↓
4. Weather API integration
       ↓
5. Thinking Machines integration
       ↓
6. Backboard memory
       ↓
7. DevRelay MCP tool integration
       ↓
8. RAG gardening knowledge
       ↓
9. Daily Garden Plan agent
       ↓
10. Frontend
       ↓
11. Render deployment
       ↓
12. Testing & documentation
```

The project should first achieve a working end-to-end flow before adding advanced features.

---

# 22. Success Criteria

GardenBuddy will be considered successful when a user can:

1. Create a garden.
2. Add plants.
3. Provide relevant garden information.
4. Retrieve weather information.
5. Allow the AI agent to reason about the garden and weather.
6. Receive a personalized daily garden plan.
7. Complete the recommended outdoor activities.
8. Record what happened.
9. Have relevant information remembered for future recommendations.

The final experience should demonstrate:

> **AI reasoning + memory + real-world tools → useful outdoor action.**