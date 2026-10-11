# Security Policy — GardenBuddy

## 1. Overview
GardenBuddy is designed with security and privacy by design, particularly regarding external AI services, user garden data, and API credentials.

---

## 2. Secrets and Environment Variables
- **Zero Secrets in Code**: No API keys, passwords, connection strings, or access tokens should ever be hardcoded into source code or committed to git.
- **Environment Isolation**: All credentials (e.g., `WEATHER_API_KEY`, `BACKBOARD_API_KEY`, `THINKING_MACHINES_API_KEY`, `DATABASE_URL`) must be loaded strictly via environment variables or managed cloud secret stores (such as Render Environment Variables).
- **Template Safety**: [.env.example](.env.example) contains only placeholder values and is safe for version control. Real `.env` files are ignored by git in [.gitignore](.gitignore).

---

## 3. Database Security
- Connections to PostgreSQL are parameterized using SQLAlchemy ORM to prevent SQL injection vulnerabilities.
- Production database URLs must use TLS/SSL encryption where supported by cloud providers.
- Local fallback uses an isolated SQLite file for development without exposing production schemas or connections.

---

## 4. AI & Tool Safety (DevRelay MCP & Thinking Machines)
- The AI reasoning layer receives only garden and plant context relevant to the user's daily tasks.
- DevRelay MCP tools are sandboxed and restricted strictly to safe gardening capabilities (e.g., weather forecasts).
- No arbitrary code execution or unvalidated system calls are performed by the AI agent.

---

## 5. Reporting a Vulnerability
If you discover a security vulnerability within GardenBuddy:
1. Please do **not** open a public issue.
2. Report the vulnerability privately to the project maintainers.
3. Include detailed steps to reproduce the issue and any relevant system context.

We will acknowledge reports promptly and coordinate a patch before disclosure.

