import os
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """GardenBuddy configuration settings."""

    APP_NAME: str = "GardenBuddy"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # CORS origins: typed as Union[str, List[str]] so pydantic-settings doesn't force json.loads on plain string env vars
    ALLOWED_ORIGINS: Union[str, List[str]] = ["*"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    loaded = json.loads(v)
                    if isinstance(loaded, list):
                        return [str(o).strip().rstrip("/").strip("'\"") for o in loaded if o]
                except Exception:
                    pass
                v = v[1:-1]
            origins = []
            for item in v.split(","):
                cleaned = item.strip().strip("'\"").rstrip("/")
                if cleaned:
                    origins.append(cleaned)
            return origins if origins else ["*"]
        elif isinstance(v, list):
            return [str(o).strip().rstrip("/").strip("'\"") for o in v if o]
        return ["*"]

    # Database Configuration (PostgreSQL in production/env, SQLite local dev fallback)
    DATABASE_URL: Optional[str] = "sqlite:///./gardenbuddy.db"

    # External Integrations (Phases 4-7)
    WEATHER_API_KEY: Optional[str] = None
    BACKBOARD_API_KEY: Optional[str] = None
    BACKBOARD_API_URL: str = "https://api.backboard.io/v1"
    THINKING_MACHINES_API_KEY: Optional[str] = None
    THINKING_MACHINES_API_URL: str = "https://api.thinkingmachines.ai/v1"
    THINKING_MACHINES_MODEL: str = "thinking-machines-default"
    DEVRELAY_GATEWAY_URL: Optional[str] = "http://localhost:8080"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

