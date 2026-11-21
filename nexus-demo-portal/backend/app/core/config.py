import os
from typing import List, Union
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    APP_NAME: str = "NEXUS-Demo-Portal-Backend"
    SERVICE_NAME: str = "nexus-demo-backend"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./nexus_demo.db"

    # Security
    SECRET_KEY: str = "dev-secret-key-nexus-observe-2026-cicada-hackathon-security"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Observability
    LOG_LEVEL: str = "INFO"
    ENABLE_METRICS: bool = True

    # Controlled Failure Simulator
    ENABLE_FAILURE_SIMULATOR: bool = True
    SIMULATION_AUTH_KEY: str = "dev-nexus-simulation-key-2026"
    MAX_SIMULATION_DURATION_SECONDS: int = 300

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            import json
            try:
                parsed = json.loads(self.CORS_ORIGINS)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return ["*"]


settings = Settings()
