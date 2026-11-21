"""Central SaaS Settings and Configuration Management"""

from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict


class CentralSaaSSettings(BaseSettings):
    ENVIRONMENT: str = "development"
    APP_NAME: str = "NEXUS-Central-SaaS"
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./central_saas.db"

    # Collector Ingestion Authentication
    COLLECTOR_API_KEY: str = "nexus-collector-auth-key-cicada-2026"

    # Engineer Authentication & Session
    SECRET_KEY: str = "nexus-central-saas-engineer-jwt-secret-cicada-2026-privacy"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ENGINEER_USERNAME: str = "engineer"
    ENGINEER_PASSWORD_HASH: str = "$2b$12$fNrVmcz2gFecSTX5zLVMFecgBi.A0OJl89NrmAxg3r648xipPBVxa"  # default: engineer123!

    # Health & Anomaly Thresholds
    STALE_TELEMETRY_THRESHOLD_SECONDS: int = 60
    CPU_EXCELLENT_MAX: float = 50.0
    CPU_GOOD_MAX: float = 70.0
    CPU_FAIR_MAX: float = 85.0
    MEMORY_EXCELLENT_MAX: float = 60.0
    MEMORY_GOOD_MAX: float = 75.0
    MEMORY_FAIR_MAX: float = 90.0

    # Local Collector Endpoint (for reverse resolution status queries if needed)
    LOCAL_COLLECTOR_URL: str = "http://localhost:8001"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8002",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
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
                return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return ["*"]


settings = CentralSaaSSettings()
