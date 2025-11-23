"""Compliance management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.core.security import require_viewer, require_noc_engineer
from app.services.compliance_service import compliance_service
from app.models.compliance import (
    ComplianceFramework,
    ComplianceControl,
    ComplianceStatus,
    ComplianceAuditLog,
)
from pydantic import BaseModel

router = APIRouter(prefix="/compliance", tags=["Compliance"])


class StatusUpdateRequest(BaseModel):
    """Request to update control status."""
    status: ComplianceStatus
    notes: Optional[str] = None


@router.get("/summary")
async def get_compliance_summary(user: dict = Depends(require_viewer)):
    """Get overall compliance summary across all frameworks."""
    return await compliance_service.get_compliance_summary()


@router.get("/frameworks", response_model=List[ComplianceFramework])
async def list_frameworks(user: dict = Depends(require_viewer)):
    """List all compliance frameworks."""
    return await compliance_service.list_frameworks()


@router.get("/frameworks/{framework_id}", response_model=ComplianceFramework)
async def get_framework(
    framework_id: str,
    user: dict = Depends(require_viewer)
):
    """Get a specific compliance framework."""
    framework = await compliance_service.get_framework(framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    return framework


@router.get(
    "/frameworks/{framework_id}/controls/{control_id}",
    response_model=ComplianceControl
)
async def get_control(
    framework_id: str,
    control_id: str,
    user: dict = Depends(require_viewer)
):
    """Get a specific control from a framework."""
    control = await compliance_service.get_control(framework_id, control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@router.patch(
    "/frameworks/{framework_id}/controls/{control_id}",
    response_model=ComplianceControl
)
async def update_control_status(
    framework_id: str,
    control_id: str,
    update: StatusUpdateRequest,
    user: dict = Depends(require_noc_engineer)
):
    """Update the status of a compliance control."""
    control = await compliance_service.update_control_status(
        framework_id=framework_id,
        control_id=control_id,
        new_status=update.status,
        performed_by=user.get("email", "unknown"),
        notes=update.notes
    )
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@router.get("/audit-logs", response_model=List[ComplianceAuditLog])
async def get_audit_logs(
    framework_id: Optional[str] = Query(None),
    control_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    user: dict = Depends(require_viewer)
):
    """Get compliance audit logs."""
    return await compliance_service.get_audit_logs(
        framework_id=framework_id,
        control_id=control_id,
        limit=limit
    )
