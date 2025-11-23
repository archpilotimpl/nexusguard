"""Incident management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.core.security import require_viewer, require_noc_engineer
from app.services.incident_service import incident_service
from app.models.schemas import (
    Incident,
    IncidentCreate,
    IncidentUpdate,
    IncidentStatus,
    IncidentSeverity,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=List[Incident])
async def list_incidents(
    status: Optional[IncidentStatus] = Query(None),
    severity: Optional[IncidentSeverity] = Query(None),
    region: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    user: dict = Depends(require_viewer)
):
    """List all incidents with optional filters."""
    return await incident_service.list_incidents(
        status=status,
        severity=severity,
        region=region,
        service=service,
        limit=limit,
        offset=offset
    )


@router.get("/stats")
async def get_incident_stats(user: dict = Depends(require_viewer)):
    """Get incident statistics."""
    return await incident_service.get_incident_stats()


@router.get("/{incident_id}", response_model=Incident)
async def get_incident(
    incident_id: str,
    user: dict = Depends(require_viewer)
):
    """Get a specific incident by ID."""
    incident = await incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("", response_model=Incident)
async def create_incident(
    incident_data: IncidentCreate,
    user: dict = Depends(require_noc_engineer)
):
    """Create a new incident."""
    return await incident_service.create_incident(incident_data)


@router.patch("/{incident_id}", response_model=Incident)
async def update_incident(
    incident_id: str,
    update_data: IncidentUpdate,
    user: dict = Depends(require_noc_engineer)
):
    """Update an incident."""
    incident = await incident_service.update_incident(incident_id, update_data)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/acknowledge", response_model=Incident)
async def acknowledge_incident(
    incident_id: str,
    user: dict = Depends(require_noc_engineer)
):
    """Acknowledge an incident."""
    update = IncidentUpdate(
        status=IncidentStatus.ACKNOWLEDGED,
        assigned_to=user["id"]
    )
    incident = await incident_service.update_incident(incident_id, update)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/resolve", response_model=Incident)
async def resolve_incident(
    incident_id: str,
    resolution_notes: Optional[str] = None,
    user: dict = Depends(require_noc_engineer)
):
    """Resolve an incident."""
    update = IncidentUpdate(
        status=IncidentStatus.RESOLVED,
        resolution_notes=resolution_notes
    )
    incident = await incident_service.update_incident(incident_id, update)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
