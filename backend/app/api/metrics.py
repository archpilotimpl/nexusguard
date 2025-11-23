"""Metrics API endpoints."""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.core.security import require_viewer
from app.services.prometheus_service import prometheus_service
from app.models.schemas import (
    MetricsSummary,
    TransactionMetrics,
    NetworkMetrics,
    InfrastructureMetrics,
    FirewallMetrics,
    Layer3Metrics,
    Layer4Metrics
)

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/summary", response_model=MetricsSummary)
async def get_metrics_summary(user: dict = Depends(require_viewer)):
    """Get comprehensive metrics summary for all regions."""
    return await prometheus_service.get_metrics_summary()


@router.get("/transactions", response_model=TransactionMetrics)
async def get_transaction_metrics(
    region: Optional[str] = Query(None, description="Filter by region"),
    user: dict = Depends(require_viewer)
):
    """Get transaction metrics."""
    return await prometheus_service.get_transaction_metrics(region)


@router.get("/network", response_model=NetworkMetrics)
async def get_network_metrics(
    region: Optional[str] = Query(None, description="Filter by region"),
    user: dict = Depends(require_viewer)
):
    """Get network device metrics."""
    return await prometheus_service.get_network_metrics(region)


@router.get("/infrastructure", response_model=InfrastructureMetrics)
async def get_infrastructure_metrics(
    region: Optional[str] = Query(None, description="Filter by region"),
    user: dict = Depends(require_viewer)
):
    """Get infrastructure metrics."""
    return await prometheus_service.get_infrastructure_metrics(region)


@router.get("/firewall", response_model=FirewallMetrics)
async def get_firewall_metrics(
    region: Optional[str] = Query(None, description="Filter by region"),
    user: dict = Depends(require_viewer)
):
    """Get firewall-specific metrics."""
    return await prometheus_service.get_firewall_metrics(region)


@router.get("/layer3", response_model=Layer3Metrics)
async def get_layer3_metrics(
    region: Optional[str] = Query(None, description="Filter by region"),
    user: dict = Depends(require_viewer)
):
    """Get Layer 3 router metrics including BGP and OSPF."""
    return await prometheus_service.get_layer3_metrics(region)


@router.get("/layer4", response_model=Layer4Metrics)
async def get_layer4_metrics(
    region: Optional[str] = Query(None, description="Filter by region"),
    user: dict = Depends(require_viewer)
):
    """Get Layer 4 load balancer metrics including SSL/TLS."""
    return await prometheus_service.get_layer4_metrics(region)


@router.get("/alerts")
async def get_active_alerts(user: dict = Depends(require_viewer)):
    """Get currently firing alerts from Prometheus."""
    return await prometheus_service.get_alerts()
