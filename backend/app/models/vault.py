"""HashiCorp Vault models."""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class VaultStatus(str, Enum):
    SEALED = "sealed"
    UNSEALED = "unsealed"
    STANDBY = "standby"
    ACTIVE = "active"
    ERROR = "error"
    UNKNOWN = "unknown"


class VaultSecretEngine(str, Enum):
    KV_V1 = "kv-v1"
    KV_V2 = "kv-v2"
    DATABASE = "database"
    AWS = "aws"
    SSH = "ssh"
    PKI = "pki"
    TRANSIT = "transit"


class VaultAuthMethod(str, Enum):
    TOKEN = "token"
    USERPASS = "userpass"
    APPROLE = "approle"
    KUBERNETES = "kubernetes"
    LDAP = "ldap"
    OIDC = "oidc"


class VaultConfig(BaseModel):
    """Vault connection configuration."""
    address: str = Field(description="Vault server address")
    namespace: Optional[str] = None
    auth_method: VaultAuthMethod = VaultAuthMethod.TOKEN
    tls_enabled: bool = True
    tls_verify: bool = True
    timeout: int = 30


class VaultHealth(BaseModel):
    """Vault health status."""
    status: VaultStatus
    version: Optional[str] = None
    cluster_name: Optional[str] = None
    cluster_id: Optional[str] = None
    replication_performance_mode: Optional[str] = None
    replication_dr_mode: Optional[str] = None
    server_time_utc: Optional[datetime] = None
    standby: bool = False
    sealed: bool = True
    performance_standby: bool = False


class VaultSecretPath(BaseModel):
    """Vault secret path configuration."""
    id: str
    name: str
    path: str
    engine: VaultSecretEngine
    description: Optional[str] = None
    last_accessed: Optional[datetime] = None
    access_count: int = 0


class VaultCredential(BaseModel):
    """Credential retrieved from Vault (metadata only)."""
    path: str
    key: str
    version: Optional[int] = None
    created_time: Optional[datetime] = None
    deletion_time: Optional[datetime] = None
    destroyed: bool = False


class AnsibleVaultIntegration(BaseModel):
    """Ansible playbook Vault integration configuration."""
    id: str
    playbook_id: str
    secret_paths: List[str]
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    inject_as: str = "env"  # "env", "file", "extra_vars"
    enabled: bool = True
    last_used: Optional[datetime] = None


class VaultAuditLog(BaseModel):
    """Vault operation audit log."""
    id: str
    operation: str
    path: str
    client_ip: Optional[str] = None
    client_id: Optional[str] = None
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    request_id: Optional[str] = None


class VaultPolicyRule(BaseModel):
    """Vault policy rule."""
    path: str
    capabilities: List[str]  # create, read, update, delete, list, sudo, deny


class VaultPolicy(BaseModel):
    """Vault policy."""
    name: str
    rules: List[VaultPolicyRule]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VaultSecretRequest(BaseModel):
    """Request to retrieve a secret from Vault."""
    path: str
    key: Optional[str] = None
    version: Optional[int] = None


class VaultSecretWrite(BaseModel):
    """Request to write a secret to Vault."""
    path: str
    data: Dict[str, Any]
    cas: Optional[int] = None  # Check-and-set version
