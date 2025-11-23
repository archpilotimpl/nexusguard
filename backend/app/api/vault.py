"""HashiCorp Vault API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.core.security import require_viewer, require_noc_engineer, require_admin
from app.services.vault_service import vault_service
from app.models.vault import (
    VaultConfig,
    VaultHealth,
    VaultSecretPath,
    AnsibleVaultIntegration,
    VaultPolicy,
    VaultAuditLog,
)

router = APIRouter(prefix="/vault", tags=["Vault"])


@router.get("/health", response_model=VaultHealth)
async def get_vault_health(user: dict = Depends(require_viewer)):
    """Get Vault health status."""
    return await vault_service.get_health()


@router.get("/summary")
async def get_vault_summary(user: dict = Depends(require_viewer)):
    """Get Vault configuration summary."""
    return await vault_service.get_vault_summary()


@router.get("/config", response_model=VaultConfig)
async def get_vault_config(user: dict = Depends(require_noc_engineer)):
    """Get current Vault configuration."""
    return await vault_service.get_config()


@router.put("/config", response_model=VaultConfig)
async def update_vault_config(
    config: VaultConfig,
    user: dict = Depends(require_admin)
):
    """Update Vault configuration."""
    return await vault_service.update_config(config)


@router.get("/secret-paths", response_model=List[VaultSecretPath])
async def list_secret_paths(user: dict = Depends(require_viewer)):
    """List all configured secret paths."""
    return await vault_service.list_secret_paths()


@router.get("/secret-paths/{path_id}", response_model=VaultSecretPath)
async def get_secret_path(
    path_id: str,
    user: dict = Depends(require_viewer)
):
    """Get a specific secret path configuration."""
    path = await vault_service.get_secret_path(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="Secret path not found")
    return path


@router.post("/secret-paths", response_model=VaultSecretPath)
async def add_secret_path(
    path: VaultSecretPath,
    user: dict = Depends(require_noc_engineer)
):
    """Add a new secret path configuration."""
    return await vault_service.add_secret_path(path)


@router.delete("/secret-paths/{path_id}")
async def delete_secret_path(
    path_id: str,
    user: dict = Depends(require_admin)
):
    """Delete a secret path configuration."""
    success = await vault_service.delete_secret_path(path_id)
    if not success:
        raise HTTPException(status_code=404, detail="Secret path not found")
    return {"message": "Secret path deleted"}


@router.get("/ansible-integrations", response_model=List[AnsibleVaultIntegration])
async def list_ansible_integrations(user: dict = Depends(require_viewer)):
    """List all Ansible-Vault integrations."""
    return await vault_service.list_ansible_integrations()


@router.get(
    "/ansible-integrations/{integration_id}",
    response_model=AnsibleVaultIntegration
)
async def get_ansible_integration(
    integration_id: str,
    user: dict = Depends(require_viewer)
):
    """Get a specific Ansible integration."""
    integration = await vault_service.get_ansible_integration(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration


@router.get("/ansible-integrations/playbook/{playbook_id}")
async def get_integration_for_playbook(
    playbook_id: str,
    user: dict = Depends(require_viewer)
):
    """Get integration configuration for a playbook."""
    integration = await vault_service.get_integration_for_playbook(playbook_id)
    if not integration:
        return {"message": "No integration configured for this playbook"}
    return integration


@router.post("/ansible-integrations", response_model=AnsibleVaultIntegration)
async def create_ansible_integration(
    integration: AnsibleVaultIntegration,
    user: dict = Depends(require_noc_engineer)
):
    """Create a new Ansible-Vault integration."""
    return await vault_service.create_ansible_integration(integration)


@router.put(
    "/ansible-integrations/{integration_id}",
    response_model=AnsibleVaultIntegration
)
async def update_ansible_integration(
    integration_id: str,
    integration: AnsibleVaultIntegration,
    user: dict = Depends(require_noc_engineer)
):
    """Update an existing Ansible integration."""
    result = await vault_service.update_ansible_integration(
        integration_id, integration
    )
    if not result:
        raise HTTPException(status_code=404, detail="Integration not found")
    return result


@router.delete("/ansible-integrations/{integration_id}")
async def delete_ansible_integration(
    integration_id: str,
    user: dict = Depends(require_admin)
):
    """Delete an Ansible integration."""
    success = await vault_service.delete_ansible_integration(integration_id)
    if not success:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"message": "Integration deleted"}


@router.get("/policies", response_model=List[VaultPolicy])
async def list_policies(user: dict = Depends(require_noc_engineer)):
    """List all Vault policies."""
    return await vault_service.list_policies()


@router.get("/policies/{policy_name}", response_model=VaultPolicy)
async def get_policy(
    policy_name: str,
    user: dict = Depends(require_noc_engineer)
):
    """Get a specific Vault policy."""
    policy = await vault_service.get_policy(policy_name)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.get("/audit-logs", response_model=List[VaultAuditLog])
async def get_audit_logs(
    operation: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    user: dict = Depends(require_noc_engineer)
):
    """Get Vault audit logs."""
    return await vault_service.get_audit_logs(
        operation=operation,
        limit=limit
    )


@router.post("/test-connection")
async def test_vault_connection(user: dict = Depends(require_admin)):
    """Test connection to Vault server."""
    try:
        health = await vault_service.get_health()
        return {
            "success": True,
            "status": health.status.value,
            "version": health.version,
            "sealed": health.sealed
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
