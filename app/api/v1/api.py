from fastapi import APIRouter

from app.api.v1.endpoints import users, gardens, plants, tasks, weather, knowledge, memory, ai_plan, mcp, agent

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(gardens.router, prefix="/gardens", tags=["Gardens"])
api_router.include_router(plants.router, prefix="/plants", tags=["Plants"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
api_router.include_router(memory.router, prefix="/memories", tags=["Memories"])
api_router.include_router(ai_plan.router, prefix="/ai", tags=["AI Agent"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["DevRelay MCP"])
api_router.include_router(agent.router, prefix="/agent", tags=["Daily Garden Agent"])

