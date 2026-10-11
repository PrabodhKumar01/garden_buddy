# AGENTS.md

## Instructions for Antigravity

You are the development agent for the GardenBuddy project.

Your responsibility is to help build, test, debug, document, and improve GardenBuddy according to the project's documentation.

The project is an AI-powered gardening assistant built for the Hacktoberfest 2026 "Touch Grass" theme.

---

# 1. Required Reading Order

Before making substantial changes, read:

```text
1. PROJECT.md
2. SECURITY.md
3. TASKS.md
```

Understand the relevant requirements before modifying code.

Do not ignore these files and replace their requirements with your own architecture.

---

# 2. Source of Truth

Use the following priority:

```text
User's explicit instruction
        ↓
PROJECT.md
        ↓
SECURITY.md
        ↓
AGENTS.md
        ↓
TASKS.md
        ↓
Existing project implementation
```

If a new user instruction conflicts with an existing project decision, follow the user's new explicit instruction.

---

# 3. Development Philosophy

Build GardenBuddy progressively.

Do NOT attempt to create the entire project in one uncontrolled operation.

Use the following loop:

```text
Understand
   ↓
Plan
   ↓
Implement
   ↓
Test
   ↓
Inspect
   ↓
Fix
   ↓
Document
   ↓
Move to next task
```

---

# 4. Do Not Invent Requirements

Do not add features merely because they seem useful.

For example, do not automatically add:

- Redis
- Celery
- Kafka
- Kubernetes
- Additional databases
- New AI providers
- New frameworks
- New MCP servers
- Complex microservices

If you believe a new technology is genuinely required:

1. Explain why.
2. Explain what problem it solves.
3. Explain the simpler alternative.
4. Ask the user for approval.

---

# 5. Existing Architecture

The required architecture is:

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

RAG
    ↓
Gardening knowledge

Render
    ↓
Deployment
```

Do not change this architecture without a clear reason and user approval.

---

# 6. Coding Rules

Write code that is:

- Readable
- Maintainable
- Modular
- Consistent
- Testable
- Appropriately documented

Prefer simple code over clever code.

Do not create unnecessary abstractions.

Do not duplicate business logic.

Do not put large amounts of application logic directly inside API route handlers.

---

# 7. Backend Rules

FastAPI is the backend framework.

Keep responsibilities separated where practical.

For example:

```text
Routes
  ↓
Application logic
  ↓
Data access / external services
```

Do not place API keys directly in Python files.

Do not hard-code external service credentials.

Validate incoming data.

Return appropriate HTTP status codes.

Handle expected external-service failures gracefully.

---

# 8. Database Rules

PostgreSQL is the source of structured application data.

Database models should represent actual application requirements.

Do not create unnecessary tables.

Do not delete or reset database data without explicit approval.

Do not modify unrelated databases.

Never use production-like destructive operations during development without confirmation.

---

# 9. AI Rules

Thinking Machines is responsible for reasoning.

The AI should receive appropriate context rather than blindly receiving the entire database.

Provide only relevant information.

The agent should not invent:

- Weather
- Plant history
- User preferences
- Garden state
- Retrieved knowledge

If required information is unavailable, the system should handle that situation explicitly.

---

# 10. Memory Rules

Backboard.io is for useful persistent AI memory.

Do not store every interaction as permanent memory.

Prefer meaningful information such as:

```text
User preferences
Important garden history
Plant-specific observations
Recurring user habits
Useful long-term context
```

Avoid storing unnecessary sensitive information.

---

# 11. MCP Rules

DevRelay MCP should be used as the tool-access layer.

Before calling a tool:

1. Determine whether the tool is actually needed.
2. Determine what data will be sent.
3. Determine what information will be returned.
4. Verify that the action is relevant to GardenBuddy.

Do not call unrelated tools.

Do not use MCP to access personal information.

---

# 12. RAG Rules

RAG should retrieve relevant gardening knowledge.

Do not retrieve the entire knowledge base for every request.

Retrieve information relevant to the current gardening situation.

The retrieved context should be passed to the AI in a clear manner.

---

# 13. Testing

After implementing a meaningful feature:

1. Run the relevant tests.
2. Inspect errors.
3. Fix failures.
4. Re-run tests.

Do not claim that a feature works without testing it when testing is reasonably possible.

Do not delete tests simply because they fail.

---

# 14. Git Rules

Safe read-only commands such as:

```text
git status
git diff
git log
```

are acceptable when needed.

Do not perform destructive Git operations without confirmation.

Do not:

```text
force push
delete remote branches
rewrite remote history
change repository visibility
```

without explicit user approval.

Never search for Git credentials.

---

# 15. Secrets

Never search for secrets.

Never read:

```text
.env
.env.*
*.pem
*.key
credentials.*
secrets.*
```

for the purpose of discovering credentials.

Use environment-variable names and placeholders.

Example:

```text
WEATHER_API_KEY=<configured externally>
```

Never print actual secret values.

---

# 16. File Scope

Work only with:

- The GardenBuddy project
- Files explicitly provided by the user
- Files required by the current task

Do not scan the user's entire computer.

Do not explore unrelated directories.

---

# 17. Communication

When a task is substantial, explain briefly:

1. What you are going to change.
2. Which files are affected.
3. Any important architectural decision.

Do not overwhelm the user with unnecessary implementation details.

If something is ambiguous and the ambiguity could change the architecture, ask before implementing it.

---

# 18. Before Installing Dependencies

Before adding a dependency:

1. Check whether the existing project already provides the required functionality.
2. Determine whether the dependency is necessary.
3. Avoid duplicate libraries.
4. Prefer established dependencies already compatible with the project.

Do not install packages globally unless explicitly required.

---

# 19. Before Changing Existing Code

Understand the existing implementation first.

Do not rewrite working components simply to match a personal coding preference.

Prefer small, targeted changes.

Preserve working functionality.

---

# 20. Completion Standard

Do not say:

> "Done"

unless the requested task has actually been completed.

When possible, report:

```text
Implemented:
- ...

Tested:
- ...

Remaining:
- ...
```

---

# 21. Most Important Rule

**Build the project; do not explore the user's computer.**

GardenBuddy is the scope.

The user's personal information, credentials, SSH configuration, unrelated files, and unrelated accounts are outside the scope of the project.