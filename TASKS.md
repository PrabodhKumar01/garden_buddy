# 🌱 GardenBuddy Development Tasks

This document is the execution roadmap for GardenBuddy.

Antigravity should work through these tasks progressively.

Do not skip ahead unnecessarily.

A task should be considered complete only after implementation and appropriate testing.

---

# Phase 0 — Project Preparation

## 0.1 Read Project Documentation

- [ ] Read `PROJECT.md`
- [ ] Read `AGENTS.md`
- [ ] Read `SECURITY.md`
- [ ] Read this `TASKS.md`

### Purpose

Understand the project before changing code.

---

## 0.2 Inspect Existing Project

- [ ] Identify existing files.
- [ ] Identify existing backend/frontend structure.
- [ ] Identify existing dependencies.
- [ ] Do not delete existing work without understanding it.

---

# Phase 1 — Backend Foundation

## 1.1 Create FastAPI Application

- [ ] Create the FastAPI application.
- [ ] Create the backend structure.
- [ ] Add a basic health endpoint.
- [ ] Verify the application starts correctly.

Expected result:

```text
GET /health
```

returns a successful response.

---

## 1.2 PostgreSQL Configuration

- [ ] Configure PostgreSQL connection.
- [ ] Use environment configuration.
- [ ] Do not hard-code credentials.
- [ ] Verify the application can connect to the database.

---

# Phase 2 — Database Models

## 2.1 User

- [ ] Create the user model if authentication is required by the MVP.
- [ ] Define required fields only.
- [ ] Add validation.

---

## 2.2 Garden

- [ ] Create Garden model.
- [ ] Associate gardens with users where applicable.
- [ ] Store required garden information.

Potential information:

```text
name
location
garden_type
sunlight
```

---

## 2.3 Plant

- [ ] Create Plant model.
- [ ] Associate plants with gardens.
- [ ] Store required plant information.

Potential information:

```text
name
date_planted
location
notes
```

---

## 2.4 Garden Tasks

- [ ] Create task representation.
- [ ] Track task status.
- [ ] Associate tasks with gardens/plants where appropriate.

---

# Phase 3 — Garden APIs

## 3.1 Garden CRUD

- [x] Create garden
- [x] Read garden
- [x] Update garden
- [x] Delete garden where appropriate

---

## 3.2 Plant CRUD

- [x] Add plant
- [x] Retrieve plants
- [x] Update plant
- [x] Remove plant where appropriate

---

## 3.3 Task APIs

- [x] Retrieve today's tasks
- [x] Mark task complete
- [x] Record relevant task result

---

# Phase 4 — Weather Integration

## 4.1 Weather Provider

- [x] Configure the Weather API.
- [x] Store credentials through environment configuration.
- [x] Do not expose the API key.

---

## 4.2 Weather Tool

- [x] Determine the required weather tool interface.
- [x] Integrate weather access through DevRelay MCP.
- [x] Retrieve current/forecast information.
- [x] Handle unavailable weather data gracefully.

---

## 4.3 Weather Testing

Test cases should include:

- [x] Valid weather request
- [x] Invalid location
- [x] Weather provider failure
- [x] Missing configuration
- [x] Unexpected API response

---

# Phase 5 — Gardening Knowledge / RAG

## 5.1 Knowledge Base

Create a focused gardening knowledge source.

Potential topics:

```text
Plant requirements
Watering
Sunlight
Soil
Planting
Seasonal gardening
Pests
Common plant problems
```

---

## 5.2 Retrieval

- [x] Implement relevant knowledge retrieval.
- [x] Retrieve only relevant context.
- [x] Handle no-result situations.

---

## 5.3 RAG Testing

- [x] Verify relevant knowledge is retrieved.
- [x] Verify irrelevant knowledge is minimized.
- [x] Verify retrieved information reaches the AI reasoning layer.

---

# Phase 6 — Backboard Memory

## 6.1 Backboard Configuration

- [x] Configure Backboard integration.
- [x] Keep credentials outside source code.
- [x] Verify connectivity.

---

## 6.2 Memory Creation

Determine what information is useful as long-term AI memory.

Examples:

```text
User gardening preferences
Important plant observations
Long-term garden history
Recurring gardening habits
```

---

## 6.3 Memory Retrieval

- [x] Retrieve relevant memories.
- [x] Avoid retrieving unrelated memory.
- [x] Pass only relevant memory to the AI.

---

# Phase 7 — Thinking Machines

## 7.1 AI Integration

- [x] Configure Thinking Machines.
- [x] Use environment configuration for credentials.
- [x] Create the GardenBuddy AI interaction.

---

## 7.2 Garden Context

The AI should receive relevant:

```text
Garden state
Plant information
Weather
Retrieved gardening knowledge
Relevant memory
```

---

## 7.3 Daily Garden Plan

Implement the main AI capability:

```text
Garden
+
Plants
+
Weather
+
Knowledge
+
Memory
        ↓
Thinking Machines
        ↓
Today's Garden Plan
```

---

## 7.4 AI Failure Handling

Handle:

- [x] AI service unavailable
- [x] Invalid AI response
- [x] Timeout
- [x] Missing context
- [x] Tool failure

The application should fail gracefully.

---

# Phase 8 — Agent Tool Workflow

## 8.1 Tool Decision

The agent should determine when it actually needs weather information.

---

## 8.2 MCP Workflow

Expected flow:

```text
Thinking Machines
       ↓
DevRelay MCP
       ↓
Weather Tool
       ↓
Weather API
       ↓
Weather Result
       ↓
Thinking Machines
```

---

## 8.3 Tool Safety

- [x] Verify tool inputs.
- [x] Avoid unnecessary data transmission.
- [x] Handle tool errors.
- [x] Do not expose credentials.

---

# Phase 9 — Daily Garden Agent

This is the core product feature.

## 9.1 Daily Plan Generation

- [x] Retrieve garden state.
- [x] Retrieve relevant memory.
- [x] Determine weather requirement.
- [x] Retrieve weather through the tool.
- [x] Retrieve relevant gardening knowledge.
- [x] Send context to Thinking Machines.
- [x] Generate daily plan.
- [x] Return structured result.

---

## 9.2 Daily Plan Content

The plan should contain useful real-world actions.

Example:

```text
🌱 Today's Garden Plan

1. Check tomato soil moisture.
2. Inspect leaves.
3. Harvest mature coriander.
4. Do not water if the soil is already sufficiently moist.
```

---

# Phase 10 — Frontend

## 10.1 Garden Dashboard

- [x] Display garden.
- [x] Display plants.
- [x] Display today's plan.
- [x] Display task status.

---

## 10.2 Plant Management

- [x] Add plant
- [x] View plant
- [x] Edit plant
- [x] Remove plant where appropriate

---

## 10.3 Daily Plan

The main screen should make the recommended real-world actions obvious.

The UI should encourage:

```text
Read plan
   ↓
Go outside
   ↓
Complete tasks
```

Do not design the application around endless AI conversation.

---

# Phase 11 — Task Completion

- [x] Allow task completion.
- [x] Record relevant observations.
- [x] Update garden state.
- [x] Update useful AI memory where appropriate.

---

# Phase 12 — Testing

## Backend

- [x] API tests
- [x] Validation tests
- [x] Database tests
- [x] Error handling tests

## AI

- [x] Context construction
- [x] Tool invocation
- [x] Memory retrieval
- [x] RAG retrieval
- [x] Daily plan generation

## Integration

- [x] Backend → PostgreSQL
- [x] Backend → Weather capability
- [x] Backend → Backboard
- [x] Backend → Thinking Machines
- [x] Agent → MCP

---

# Phase 13 — Deployment

## Render

- [x] Prepare production configuration.
- [x] Configure environment variables.
- [x] Deploy backend.
- [x] Verify health endpoint.
- [x] Verify database connectivity.
- [x] Verify external integrations.

Never put real credentials into source code.

---

# Phase 14 — Documentation

- [x] Update README.
- [x] Document setup.
- [x] Document environment variables.
- [x] Document architecture.
- [x] Document major API functionality.
- [x] Document how the AI agent works.
- [x] Document Hacktoberfest theme alignment.

---

# Phase 15 — Final Validation

Before declaring the MVP complete:

- [x] User can create a garden.
- [x] User can add plants.
- [x] Weather can be retrieved.
- [x] AI can reason about garden + weather.
- [x] Relevant gardening knowledge can be retrieved.
- [x] AI memory works.
- [x] Daily plan is generated.
- [x] User can complete tasks.
- [x] Application handles expected failures.
- [x] Secrets are not committed.
- [x] Security rules are respected.
- [x] Application can be deployed.

---

# Development Rule

Complete phases progressively.

Do not mark a task complete merely because code was generated.

Use:

```text
Implement
   ↓
Run
   ↓
Test
   ↓
Fix
   ↓
Verify
   ↓
Mark complete
```

If a task cannot be completed because information or credentials are missing, stop at that task and clearly explain what is required.
