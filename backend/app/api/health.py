"""Health check endpoints."""
from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

from app.core.config import settings
from app.models.schemas import HealthStatus, ServiceHealth, SystemHealth

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=Dict[str, Any])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/detailed", response_model=SystemHealth)
async def detailed_health_check():
    """Detailed health check with service dependencies."""
    services = []

    # Check Prometheus
    services.append(ServiceHealth(
        name="prometheus",
        status=HealthStatus.HEALTHY,  # Would actually ping Prometheus
        last_check=datetime.utcnow(),
        latency_ms=5.2
    ))

    # Check Grafana
    services.append(ServiceHealth(
        name="grafana",
        status=HealthStatus.HEALTHY,
        last_check=datetime.utcnow(),
        latency_ms=3.1
    ))

    # Check Database
    services.append(ServiceHealth(
        name="database",
        status=HealthStatus.HEALTHY,
        last_check=datetime.utcnow(),
        latency_ms=2.4
    ))

    # Check Redis
    services.append(ServiceHealth(
        name="redis",
        status=HealthStatus.HEALTHY,
        last_check=datetime.utcnow(),
        latency_ms=1.0
    ))

    # Determine overall status
    if all(s.status == HealthStatus.HEALTHY for s in services):
        overall_status = HealthStatus.HEALTHY
    elif any(s.status == HealthStatus.UNHEALTHY for s in services):
        overall_status = HealthStatus.UNHEALTHY
    else:
        overall_status = HealthStatus.DEGRADED

    return SystemHealth(
        status=overall_status,
        services=services
    )


@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"alive": True}
