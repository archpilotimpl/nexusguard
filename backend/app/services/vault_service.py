"""HashiCorp Vault integration service."""
import os
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.models.vault import (
    VaultStatus,
    VaultSecretEngine,
    VaultAuthMethod,
    VaultConfig,
    VaultHealth,
    VaultSecretPath,
    VaultCredential,
    AnsibleVaultIntegration,
    VaultAuditLog,
    VaultPolicy,
    VaultPolicyRule,
)

logger = get_logger(__name__)


class VaultService:
    """Service for HashiCorp Vault integration."""

    def __init__(self):
        self._config = VaultConfig(
            address=os.getenv("VAULT_ADDR", "http://vault:8200"),
            namespace=os.getenv("VAULT_NAMESPACE"),
            auth_method=VaultAuthMethod.TOKEN,
            tls_enabled=os.getenv("VAULT_TLS_ENABLED", "false").lower() == "true",
            tls_verify=os.getenv("VAULT_TLS_VERIFY", "true").lower() == "true"
        )
        self._client = None
        self._secret_paths: Dict[str, VaultSecretPath] = {}
        self._ansible_integrations: Dict[str, AnsibleVaultIntegration] = {}
        self._audit_logs: List[VaultAuditLog] = []
        self._policies: Dict[str, VaultPolicy] = {}

        self._init_sample_data()

    def _init_sample_data(self):
        """Initialize sample Vault configuration data."""
        # Sample secret paths
        sample_paths = [
            VaultSecretPath(
                id="path-1",
                name="Database Credentials",
                path="secret/data/nexusguard/database",
                engine=VaultSecretEngine.KV_V2,
                description="PostgreSQL database credentials for all regions",
                last_accessed=datetime.utcnow(),
                access_count=1250
            ),
            VaultSecretPath(
                id="path-2",
                name="API Keys",
                path="secret/data/nexusguard/api-keys",
                engine=VaultSecretEngine.KV_V2,
                description="External API keys (payment gateways, monitoring)",
                last_accessed=datetime.utcnow(),
                access_count=890
            ),
            VaultSecretPath(
                id="path-3",
                name="SSH Keys",
                path="ssh/creds/nexusguard-ansible",
                engine=VaultSecretEngine.SSH,
                description="Dynamic SSH credentials for Ansible automation",
                last_accessed=datetime.utcnow(),
                access_count=567
            ),
            VaultSecretPath(
                id="path-4",
                name="TLS Certificates",
                path="pki/issue/nexusguard",
                engine=VaultSecretEngine.PKI,
                description="Internal TLS certificates for service-to-service",
                last_accessed=datetime.utcnow(),
                access_count=234
            ),
            VaultSecretPath(
                id="path-5",
                name="AWS Credentials",
                path="aws/creds/nexusguard-backup",
                engine=VaultSecretEngine.AWS,
                description="Dynamic AWS credentials for backup operations",
                last_accessed=datetime.utcnow(),
                access_count=156
            ),
            VaultSecretPath(
                id="path-6",
                name="Encryption Keys",
                path="transit/keys/nexusguard",
                engine=VaultSecretEngine.TRANSIT,
                description="Encryption keys for data at rest",
                last_accessed=datetime.utcnow(),
                access_count=4521
            ),
            VaultSecretPath(
                id="path-7",
                name="Redis Credentials",
                path="secret/data/nexusguard/redis",
                engine=VaultSecretEngine.KV_V2,
                description="Redis cache authentication credentials",
                last_accessed=datetime.utcnow(),
                access_count=678
            ),
            VaultSecretPath(
                id="path-8",
                name="Blockchain Node Keys",
                path="secret/data/nexusguard/blockchain",
                engine=VaultSecretEngine.KV_V2,
                description="Private keys for blockchain node operations",
                last_accessed=datetime.utcnow(),
                access_count=89
            ),
        ]

        for path in sample_paths:
            self._secret_paths[path.id] = path

        # Sample Ansible integrations
        ansible_integrations = [
            AnsibleVaultIntegration(
                id="int-1",
                playbook_id="database_failover",
                secret_paths=[
                    "secret/data/nexusguard/database",
                    "secret/data/nexusguard/redis"
                ],
                environment_variables={
                    "DB_PASSWORD": "secret/data/nexusguard/database#password",
                    "DB_USER": "secret/data/nexusguard/database#username",
                    "REDIS_PASSWORD": "secret/data/nexusguard/redis#password"
                },
                inject_as="env",
                enabled=True,
                last_used=datetime.utcnow()
            ),
            AnsibleVaultIntegration(
                id="int-2",
                playbook_id="restart_application",
                secret_paths=[
                    "secret/data/nexusguard/api-keys"
                ],
                environment_variables={
                    "API_SECRET": "secret/data/nexusguard/api-keys#app_secret"
                },
                inject_as="env",
                enabled=True,
                last_used=datetime.utcnow()
            ),
            AnsibleVaultIntegration(
                id="int-3",
                playbook_id="blockchain_node_recovery",
                secret_paths=[
                    "secret/data/nexusguard/blockchain"
                ],
                environment_variables={
                    "NODE_PRIVATE_KEY": "secret/data/nexusguard/blockchain#private_key",
                    "NODE_SIGNING_KEY": "secret/data/nexusguard/blockchain#signing_key"
                },
                inject_as="file",
                enabled=True,
                last_used=datetime.utcnow()
            ),
            AnsibleVaultIntegration(
                id="int-4",
                playbook_id="ssl_certificate_check",
                secret_paths=[
                    "pki/issue/nexusguard"
                ],
                environment_variables={},
                inject_as="extra_vars",
                enabled=True
            ),
            AnsibleVaultIntegration(
                id="int-5",
                playbook_id="network_device_recovery",
                secret_paths=[
                    "ssh/creds/nexusguard-ansible"
                ],
                environment_variables={
                    "SSH_PRIVATE_KEY": "ssh/creds/nexusguard-ansible#private_key"
                },
                inject_as="file",
                enabled=True
            ),
        ]

        for integration in ansible_integrations:
            self._ansible_integrations[integration.id] = integration

        # Sample policies
        policies = [
            VaultPolicy(
                name="nexusguard-ansible",
                rules=[
                    VaultPolicyRule(
                        path="secret/data/nexusguard/*",
                        capabilities=["read", "list"]
                    ),
                    VaultPolicyRule(
                        path="ssh/creds/nexusguard-ansible",
                        capabilities=["read", "create", "update"]
                    ),
                    VaultPolicyRule(
                        path="aws/creds/nexusguard-backup",
                        capabilities=["read"]
                    ),
                ],
                created_at=datetime.utcnow()
            ),
            VaultPolicy(
                name="nexusguard-app",
                rules=[
                    VaultPolicyRule(
                        path="secret/data/nexusguard/database",
                        capabilities=["read"]
                    ),
                    VaultPolicyRule(
                        path="secret/data/nexusguard/redis",
                        capabilities=["read"]
                    ),
                    VaultPolicyRule(
                        path="transit/encrypt/nexusguard",
                        capabilities=["update"]
                    ),
                    VaultPolicyRule(
                        path="transit/decrypt/nexusguard",
                        capabilities=["update"]
                    ),
                ],
                created_at=datetime.utcnow()
            ),
            VaultPolicy(
                name="nexusguard-admin",
                rules=[
                    VaultPolicyRule(
                        path="secret/*",
                        capabilities=["create", "read", "update", "delete", "list"]
                    ),
                    VaultPolicyRule(
                        path="auth/*",
                        capabilities=["create", "read", "update", "delete", "list", "sudo"]
                    ),
                    VaultPolicyRule(
                        path="sys/*",
                        capabilities=["read", "list"]
                    ),
                ],
                created_at=datetime.utcnow()
            ),
        ]

        for policy in policies:
            self._policies[policy.name] = policy

    async def get_health(self) -> VaultHealth:
        """Get Vault health status."""
        # In production, this would query Vault's /v1/sys/health endpoint
        return VaultHealth(
            status=VaultStatus.ACTIVE,
            version="1.15.4",
            cluster_name="nexusguard-vault",
            cluster_id="vault-cluster-1234abcd",
            replication_performance_mode="disabled",
            replication_dr_mode="disabled",
            server_time_utc=datetime.utcnow(),
            standby=False,
            sealed=False,
            performance_standby=False
        )

    async def get_config(self) -> VaultConfig:
        """Get current Vault configuration."""
        return self._config

    async def update_config(self, config: VaultConfig) -> VaultConfig:
        """Update Vault configuration."""
        self._config = config
        logger.info("Vault configuration updated", address=config.address)
        return self._config

    async def list_secret_paths(self) -> List[VaultSecretPath]:
        """List all configured secret paths."""
        return list(self._secret_paths.values())

    async def get_secret_path(self, path_id: str) -> Optional[VaultSecretPath]:
        """Get a specific secret path configuration."""
        return self._secret_paths.get(path_id)

    async def add_secret_path(self, path: VaultSecretPath) -> VaultSecretPath:
        """Add a new secret path configuration."""
        if not path.id:
            path.id = str(uuid.uuid4())
        self._secret_paths[path.id] = path
        logger.info("Secret path added", path_id=path.id, path=path.path)
        return path

    async def delete_secret_path(self, path_id: str) -> bool:
        """Delete a secret path configuration."""
        if path_id in self._secret_paths:
            del self._secret_paths[path_id]
            logger.info("Secret path deleted", path_id=path_id)
            return True
        return False

    async def list_ansible_integrations(self) -> List[AnsibleVaultIntegration]:
        """List all Ansible-Vault integrations."""
        return list(self._ansible_integrations.values())

    async def get_ansible_integration(
        self, integration_id: str
    ) -> Optional[AnsibleVaultIntegration]:
        """Get a specific Ansible integration."""
        return self._ansible_integrations.get(integration_id)

    async def get_integration_for_playbook(
        self, playbook_id: str
    ) -> Optional[AnsibleVaultIntegration]:
        """Get integration configuration for a playbook."""
        for integration in self._ansible_integrations.values():
            if integration.playbook_id == playbook_id and integration.enabled:
                return integration
        return None

    async def create_ansible_integration(
        self, integration: AnsibleVaultIntegration
    ) -> AnsibleVaultIntegration:
        """Create a new Ansible-Vault integration."""
        if not integration.id:
            integration.id = str(uuid.uuid4())
        self._ansible_integrations[integration.id] = integration
        logger.info(
            "Ansible integration created",
            integration_id=integration.id,
            playbook_id=integration.playbook_id
        )
        return integration

    async def update_ansible_integration(
        self,
        integration_id: str,
        integration: AnsibleVaultIntegration
    ) -> Optional[AnsibleVaultIntegration]:
        """Update an existing Ansible integration."""
        if integration_id not in self._ansible_integrations:
            return None
        integration.id = integration_id
        self._ansible_integrations[integration_id] = integration
        logger.info("Ansible integration updated", integration_id=integration_id)
        return integration

    async def delete_ansible_integration(self, integration_id: str) -> bool:
        """Delete an Ansible integration."""
        if integration_id in self._ansible_integrations:
            del self._ansible_integrations[integration_id]
            logger.info("Ansible integration deleted", integration_id=integration_id)
            return True
        return False

    async def get_credentials_for_playbook(
        self, playbook_id: str
    ) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials from Vault for a playbook execution.
        Returns environment variables ready to be injected.
        """
        integration = await self.get_integration_for_playbook(playbook_id)
        if not integration:
            return None

        # In production, this would fetch actual secrets from Vault
        # For demo, return placeholder indicating secrets would be fetched
        credentials = {}
        for env_var, secret_path in integration.environment_variables.items():
            # Parse path#key format
            if "#" in secret_path:
                path, key = secret_path.rsplit("#", 1)
                credentials[env_var] = f"<vault:{path}:{key}>"
            else:
                credentials[env_var] = f"<vault:{secret_path}>"

        # Update last used timestamp
        integration.last_used = datetime.utcnow()
        self._ansible_integrations[integration.id] = integration

        # Log the access
        audit_log = VaultAuditLog(
            id=str(uuid.uuid4()),
            operation="read",
            path=f"playbook/{playbook_id}",
            client_id="ansible-service",
            timestamp=datetime.utcnow(),
            success=True,
            request_id=str(uuid.uuid4())
        )
        self._audit_logs.append(audit_log)

        logger.info(
            "Retrieved credentials for playbook",
            playbook_id=playbook_id,
            credential_count=len(credentials)
        )

        return credentials

    async def list_policies(self) -> List[VaultPolicy]:
        """List all Vault policies."""
        return list(self._policies.values())

    async def get_policy(self, policy_name: str) -> Optional[VaultPolicy]:
        """Get a specific policy."""
        return self._policies.get(policy_name)

    async def get_audit_logs(
        self,
        operation: Optional[str] = None,
        limit: int = 50
    ) -> List[VaultAuditLog]:
        """Get Vault audit logs with optional filters."""
        logs = self._audit_logs

        if operation:
            logs = [l for l in logs if l.operation == operation]

        logs.sort(key=lambda l: l.timestamp, reverse=True)
        return logs[:limit]

    async def get_vault_summary(self) -> Dict:
        """Get summary of Vault configuration and status."""
        health = await self.get_health()

        return {
            "status": health.status.value,
            "version": health.version,
            "sealed": health.sealed,
            "cluster_name": health.cluster_name,
            "secret_paths_count": len(self._secret_paths),
            "ansible_integrations_count": len(self._ansible_integrations),
            "enabled_integrations": sum(
                1 for i in self._ansible_integrations.values() if i.enabled
            ),
            "policies_count": len(self._policies),
            "auth_method": self._config.auth_method.value,
            "address": self._config.address,
            "engines_in_use": list(set(
                p.engine.value for p in self._secret_paths.values()
            ))
        }


# Singleton instance
vault_service = VaultService()
