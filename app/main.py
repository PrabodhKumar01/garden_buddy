from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import check_db_connection, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown events."""
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="GardenBuddy — AI Garden Weather Agent API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Assets
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Register API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/dashboard", tags=["Frontend"], include_in_schema=False)
async def dashboard():
    """Serve the GardenBuddy web frontend dashboard."""
    return FileResponse("app/static/index.html")


@app.get("/", tags=["General"])
async def root():
    """Root endpoint welcoming users and pointing to dashboard, health & docs."""
    return {
        "message": "Welcome to GardenBuddy API — AI Garden Weather Agent",
        "dashboard": "/dashboard",
        "docs": "/docs",
        "health": "/health",
        "version": settings.APP_VERSION
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint required by Phase 1.1 and cloud platforms."""
    db_status = check_db_connection()
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
