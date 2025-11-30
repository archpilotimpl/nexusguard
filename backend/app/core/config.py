"""Application configuration settings."""
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "NexusGuard NOC"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3090", "http://localhost:8090"]

    # Security
    SECRET_KEY: str = Field(..., description="Secret key for JWT encoding")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "RS256"

    # Auth0 Configuration - reads from .env if set
    # Default to False to use local JWT, set to True in .env to enable Auth0
    ENABLE_AUTH0: bool = True
    AUTH0_DOMAIN: Optional[str] = None  # e.g., nexusguard.us.auth0.com (without https://)
    AUTH0_CLIENT_ID: Optional[str] = None
    AUTH0_CLIENT_SECRET: Optional[str] = None
    AUTH0_API_IDENTIFIER: Optional[str] = None
    # If True, skip signature and issuer/audience verification and return unverified claims
    AUTH0_SKIP_VERIFICATION: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nocuser:nocpassword@localhost:5432/nexusguard"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Prometheus
    PROMETHEUS_URL: str = "http://localhost:9090"
    PROMETHEUS_FEDERATION_URLS: dict = {
        "india": "http://prometheus-india:9090",
        "china": "http://prometheus-china:9090",
        "usa": "http://prometheus-usa:9090"
    }

    # Grafana
    GRAFANA_URL: str = "http://localhost:3001"
    GRAFANA_API_KEY: Optional[str] = None

    # Ansible
    ANSIBLE_PLAYBOOKS_PATH: str = "/opt/nexusguard/ansible/playbooks"
    ANSIBLE_INVENTORY_PATH: str = "/opt/nexusguard/ansible/inventory"
    ANSIBLE_ROLES_PATH: str = "/opt/nexusguard/ansible/roles"
    ANSIBLE_PRIVATE_KEY: Optional[str] = None

    # Alerting
    ALERTMANAGER_URL: str = "http://localhost:9093"
    SLACK_WEBHOOK_URL: Optional[str] = None
    PAGERDUTY_INTEGRATION_KEY: Optional[str] = None

    # Geo Configuration
    SUPPORTED_REGIONS: List[str] = ["india", "china", "usa"]
    DEFAULT_REGION: str = "usa"

    # Data Retention
    METRICS_RETENTION_DAYS: int = 90
    INCIDENT_RETENTION_DAYS: int = 365

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
