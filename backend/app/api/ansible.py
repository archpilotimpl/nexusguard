"""Ansible playbook API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.core.security import require_viewer, require_noc_engineer, require_admin
from app.services.ansible_service import ansible_service
from app.models.schemas import (
    Playbook,
    PlaybookExecution,
    PlaybookExecutionRequest,
)

router = APIRouter(prefix="/ansible", tags=["Ansible"])


@router.get("/playbooks", response_model=List[Playbook])
async def list_playbooks(
    category: Optional[str] = Query(None, description="Filter by category"),
    user: dict = Depends(require_viewer)
):
    """List all available Ansible playbooks."""
    return await ansible_service.list_playbooks(category)


@router.get("/playbooks/{playbook_id}", response_model=Playbook)
async def get_playbook(
    playbook_id: str,
    user: dict = Depends(require_viewer)
):
    """Get a specific playbook by ID."""
    playbook = await ansible_service.get_playbook(playbook_id)
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return playbook


@router.post("/run-playbook", response_model=PlaybookExecution)
async def run_playbook(
    request: PlaybookExecutionRequest,
    user: dict = Depends(require_noc_engineer)
):
    """Execute an Ansible playbook."""
    try:
        execution = await ansible_service.execute_playbook(
            request=request,
            executed_by=user["id"]
        )
        return execution
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute playbook: {str(e)}")


@router.get("/executions", response_model=List[PlaybookExecution])
async def list_executions(
    playbook_id: Optional[str] = Query(None),
    incident_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    user: dict = Depends(require_viewer)
):
    """List playbook executions."""
    return await ansible_service.list_executions(
        playbook_id=playbook_id,
        incident_id=incident_id,
        limit=limit
    )


@router.get("/executions/{execution_id}", response_model=PlaybookExecution)
async def get_execution(
    execution_id: str,
    user: dict = Depends(require_viewer)
):
    """Get playbook execution status."""
    execution = await ansible_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    user: dict = Depends(require_admin)
):
    """Cancel a running playbook execution."""
    success = await ansible_service.cancel_execution(execution_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel execution (not found or not running)"
        )
    return {"status": "cancelled", "execution_id": execution_id}
