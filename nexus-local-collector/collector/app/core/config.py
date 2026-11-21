"""Central configuration management using Pydantic Settings."""
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict


class CollectorSettings(BaseSettings):
    ENVIRONMENT: str = "development"
    COLLECTOR_ID: str = "collector-demo-001"
    APP_NAME: str = "NEXUS-Local-Collector"
    COLLECTOR_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    LOG_LEVEL: str = "INFO"
    COLLECTION_TIMEOUT_SECONDS: float = 3.0
    COLLECTION_INTERVAL_SECONDS: int = 6

    # Monitored Target: NEXUS Demo Portal
    DEMO_PORTAL_BASE_URL: str = "http://127.0.0.1:8000"
    DEMO_PORTAL_API_URL: str = "http://127.0.0.1:8000/api/v1"
    DEMO_PORTAL_METRICS_URL: str = "http://127.0.0.1:8000/metrics"
    DEMO_PORTAL_HEALTH_URL: str = "http://127.0.0.1:8000/api/v1/health"

    # Outbound Egress Target: Central SaaS
    CENTRAL_SAAS_URL: str = "http://127.0.0.1:8002/api/v1/ingest"
    CENTRAL_SAAS_API_KEY: str = "nexus-collector-auth-key-cicada-2026"

    # Security & Admin Approval
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: str = "$2b$12$SOCEgh7BAewu1LUmiSqNHumneCIARRWhLZprGzPTGLnEYKSwK7R1S"  # default: admin123!
    SECRET_KEY: str = "nexus-local-collector-session-key-2026-cicada-privacy"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REQUIRE_HUMAN_APPROVAL: bool = True

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:8001", "http://127.0.0.1:8001"]

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
                return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return ["*"]


settings = CollectorSettings()
