# Figure 4: Vault-Integrated Playbook Execution

```mermaid
graph TB
    subgraph "Configuration Phase"
        Admin[NOC Administrator]
        VaultConfig[Vault Configuration<br/>Secret Paths & Policies]
        Integration[Ansible-Vault Integration<br/>Playbook-to-Secret Mapping]

        Admin --> VaultConfig
        Admin --> Integration
    end

    subgraph "HashiCorp Vault (500)"
        VaultServer[Vault Server<br/>Production Mode + TLS]

        subgraph "Secret Engines (520)"
            KVEngine[KV v2 Engine<br/>secret/data/nexusguard/*]
            SSHEngine[SSH Engine<br/>ssh/creds/nexusguard-ansible]
            PKIEngine[PKI Engine<br/>pki/issue/nexusguard]
            AWSEngine[AWS Engine<br/>aws/creds/nexusguard-backup]
            TransitEngine[Transit Engine<br/>transit/keys/nexusguard]
            DBEngine[Database Engine<br/>database/creds/nexusguard]
        end

        subgraph "Policies (530)"
            AnsiblePolicy[nexusguard-ansible<br/>Read: secret/*, ssh/*]
            AppPolicy[nexusguard-app<br/>Read: secret/*, transit/*]
            AdminPolicy[nexusguard-admin<br/>Full Access: *]
        end

        VaultServer --> KVEngine
        VaultServer --> SSHEngine
        VaultServer --> PKIEngine
        VaultServer --> AWSEngine
        VaultServer --> TransitEngine
        VaultServer --> DBEngine

        AnsiblePolicy --> VaultServer
        AppPolicy --> VaultServer
        AdminPolicy --> VaultServer
    end

    subgraph "Execution Request Flow"
        Frontend[Dashboard UI]
        PlaybookReq[Playbook Execution Request<br/>POST /api/v1/ansible/run-playbook]

        Frontend --> PlaybookReq
    end

    subgraph "Ansible Service (240)"
        AnsibleSvc[Ansible Service]
        AuthCheck[Authorization Check<br/>User Role: noc_engineer]
        GetIntegration[Fetch Integration Config<br/>playbook_id → secret_paths]

        PlaybookReq --> AnsibleSvc
        AnsibleSvc --> AuthCheck
        AuthCheck --> GetIntegration
    end

    subgraph "Vault Service (260)"
        VaultSvc[Vault Service]
        Authenticate[Authenticate to Vault<br/>AppRole Method]
        FetchSecrets[Fetch Secrets<br/>Multiple Paths in Parallel]
        BuildCredMap[Build Credential Map<br/>ENV vars / Files / Extra Vars]
        AuditLog[Audit Log Entry<br/>user, timestamp, paths]

        VaultSvc --> Authenticate
        Authenticate --> FetchSecrets
        FetchSecrets --> BuildCredMap
        FetchSecrets --> AuditLog
    end

    subgraph "Credential Injection (2100)"
        InjectionDecision{Injection<br/>Method?}

        EnvInject[Environment Variables<br/>DB_PASSWORD=xxx<br/>Added to subprocess env]

        FileInject[Temporary Files<br/>Write to /tmp/secure/<br/>chmod 0600]

        ExtraVarsInject[Ansible Extra Vars<br/>JSON format with db_config]

        InjectionDecision -->|inject_as=env| EnvInject
        InjectionDecision -->|inject_as=file| FileInject
        InjectionDecision -->|inject_as=extra_vars| ExtraVarsInject
    end

    subgraph "Ansible Execution Engine (620)"
        BuildCmd[Build ansible-playbook Command<br/>+ inventory + extra-vars]
        Execute[Execute Subprocess<br/>with Credentials Injected]
        CaptureOutput[Capture stdout/stderr<br/>Real-time Streaming]
        Cleanup[Cleanup Temp Files<br/>Remove Credential Traces]

        BuildCmd --> Execute
        Execute --> CaptureOutput
        CaptureOutput --> Cleanup
    end

    subgraph "Audit & Compliance (3300)"
        VaultAuditDB[(Vault Audit Logs<br/>PostgreSQL)]
        ComplianceCheck[Compliance Control Update<br/>If remediation successful]

        VaultAuditDB --> ComplianceCheck
    end

    subgraph "Result Flow"
        UpdateExecution[Update PlaybookExecution<br/>status, output, error]
        UpdateIncident[Update Incident<br/>Link execution_id]
        NotifyUser[Notify User<br/>WebSocket / Dashboard]

        UpdateExecution --> UpdateIncident
        UpdateIncident --> NotifyUser
    end

    %% Connections
    VaultConfig --> VaultServer
    Integration --> GetIntegration

    GetIntegration --> VaultSvc

    VaultSvc --> VaultServer
    VaultServer --> FetchSecrets

    BuildCredMap --> InjectionDecision

    EnvInject --> BuildCmd
    FileInject --> BuildCmd
    ExtraVarsInject --> BuildCmd

    BuildCmd --> Execute

    AuditLog --> VaultAuditDB

    Cleanup --> UpdateExecution

    style Admin fill:#e1f5ff
    style VaultConfig fill:#ffe1e1
    style Integration fill:#ffe1e1

    style VaultServer fill:#ffe1e1
    style KVEngine fill:#fff4e1
    style SSHEngine fill:#fff4e1
    style PKIEngine fill:#fff4e1
    style AWSEngine fill:#fff4e1
    style TransitEngine fill:#fff4e1
    style DBEngine fill:#fff4e1

    style AnsiblePolicy fill:#e1ffe1
    style AppPolicy fill:#e1ffe1
    style AdminPolicy fill:#e1ffe1

    style Frontend fill:#e1f5ff
    style AnsibleSvc fill:#fff4e1
    style VaultSvc fill:#ffe1e1

    style EnvInject fill:#f0e1ff
    style FileInject fill:#f0e1ff
    style ExtraVarsInject fill:#f0e1ff

    style Execute fill:#ffe1f5
    style VaultAuditDB fill:#f0e1ff
```

## Detailed Component Descriptions

### Configuration Phase (1800)

#### Vault Secret Paths (1810)
Administrators register secrets in Vault engines:

**KV v2 Engine (Database Credentials)**
```bash
vault kv put secret/nexusguard/database \
  host=postgres.nexusguard.internal \
  port=5432 \
  username=nexusguard_app \
  password=SecureDbPass123 \
  database=nexusguard_prod
```

**KV v2 Engine (Redis Credentials)**
```bash
vault kv put secret/nexusguard/redis \
  host=redis.nexusguard.internal \
  port=6379 \
  password=SecureRedisPass456
```

**SSH Engine (Dynamic Credentials)**
```bash
vault write ssh/roles/nexusguard-ansible \
  key_type=otp \
  default_user=ansible \
  cidr_list=10.0.0.0/8
```

**PKI Engine (TLS Certificates)**
```bash
vault write pki/issue/nexusguard \
  common_name=api.nexusguard.internal \
  ttl=8760h
```

#### Ansible-Vault Integration Mapping (1820)
```json
{
  "id": "int-database-failover",
  "playbook_id": "database_failover",
  "secret_paths": [
    "secret/data/nexusguard/database",
    "secret/data/nexusguard/redis"
  ],
  "environment_variables": {
    "DB_HOST": "secret/data/nexusguard/database#host",
    "DB_PORT": "secret/data/nexusguard/database#port",
    "DB_USER": "secret/data/nexusguard/database#username",
    "DB_PASSWORD": "secret/data/nexusguard/database#password",
    "DB_NAME": "secret/data/nexusguard/database#database",
    "REDIS_HOST": "secret/data/nexusguard/redis#host",
    "REDIS_PASSWORD": "secret/data/nexusguard/redis#password"
  },
  "inject_as": "env",
  "enabled": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_used": null
}
```

---

### Execution Request Flow (1900)

#### API Request (1910)
```http
POST /api/v1/ansible/run-playbook
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "playbook_id": "database_failover",
  "incident_id": "INC-2024-0120-1500",
  "parameters": {
    "primary_db": "postgres-primary-01",
    "replica_db": "postgres-replica-02"
  },
  "target_hosts": ["postgres-replica-02"],
  "dry_run": false
}
```

#### Authorization Check (1920)
```python
def authorize_playbook_execution(user: dict, playbook: Playbook):
    # Check role
    if user["role"] not in ["admin", "noc_engineer"]:
        raise HTTPException(403, "Insufficient permissions")

    # Check approval requirement
    if playbook.requires_approval and not request.approved:
        raise HTTPException(400, "Approval required")

    return True
```

---

### Credential Retrieval (2000)

#### Vault Authentication (2020)
```python
import hvac

# Initialize Vault client
vault_client = hvac.Client(
    url="https://vault.nexusguard.internal:8200",
    namespace="nexusguard"
)

# Authenticate using AppRole
vault_client.auth.approle.login(
    role_id=os.environ["VAULT_ROLE_ID"],
    secret_id=os.environ["VAULT_SECRET_ID"]
)

# Verify authentication
if not vault_client.is_authenticated():
    raise VaultAuthenticationError("Failed to authenticate")
```

#### Secret Retrieval (2030)
```python
credentials = {}

for env_var, secret_spec in integration.environment_variables.items():
    # Parse "secret/data/nexusguard/database#password"
    path, key = secret_spec.rsplit('#', 1)

    # Fetch from KV v2 engine
    response = vault_client.secrets.kv.v2.read_secret_version(
        path=path.replace("secret/data/", ""),
        mount_point="secret"
    )

    # Extract specific key
    secret_value = response['data']['data'][key]

    # Add to credentials map
    credentials[env_var] = secret_value

# Result:
# credentials = {
#   "DB_HOST": "postgres.nexusguard.internal",
#   "DB_PORT": "5432",
#   "DB_USER": "nexusguard_app",
#   "DB_PASSWORD": "SecureDbPass123",
#   "DB_NAME": "nexusguard_prod",
#   "REDIS_HOST": "redis.nexusguard.internal",
#   "REDIS_PASSWORD": "SecureRedisPass456"
# }
```

#### Audit Logging (2040)
```python
audit_log = VaultAuditLog(
    id=generate_uuid(),
    operation="read_secret",
    path="secret/data/nexusguard/database",
    user=user.email,
    playbook_execution_id=execution.id,
    timestamp=datetime.utcnow(),
    success=True,
    client_ip=request.client.host
)

db.session.add(audit_log)
db.session.commit()
```

---

### Credential Injection Methods (2100)

#### Method 1: Environment Variables (2110)
**Use Case**: Most common, works with all playbooks

```python
# Build execution environment
execution_env = {
    **os.environ,  # Inherit system environment
    **credentials,  # Add Vault credentials
    "ANSIBLE_HOST_KEY_CHECKING": "False",
    "ANSIBLE_STDOUT_CALLBACK": "json"
}

# Playbook can access via lookup
# - name: Connect to database
#   postgresql_db:
#     login_host: "{{ lookup('env', 'DB_HOST') }}"
#     login_user: "{{ lookup('env', 'DB_USER') }}"
#     login_password: "{{ lookup('env', 'DB_PASSWORD') }}"
```

**Security**:
- ✓ Not visible in `ps aux` (only playbook path shown)
- ✓ Not written to disk
- ✓ Scoped to subprocess only
- ✓ Automatically cleaned when process exits

---

#### Method 2: Temporary Files (2120)
**Use Case**: SSH private keys, TLS certificates, large secrets

```python
# Create secure temporary directory
temp_dir = tempfile.mkdtemp(prefix="nexusguard_ansible_")
os.chmod(temp_dir, 0o700)  # Owner-only access (rwx------)

# Write SSH private key
ssh_key_path = os.path.join(temp_dir, "id_rsa")
with open(ssh_key_path, 'w') as f:
    f.write(credentials["SSH_PRIVATE_KEY"])
os.chmod(ssh_key_path, 0o600)  # Owner-only read/write (rw-------)

# Write TLS certificate
cert_path = os.path.join(temp_dir, "tls_cert.pem")
with open(cert_path, 'w') as f:
    f.write(credentials["TLS_CERTIFICATE"])
os.chmod(cert_path, 0o600)

# Pass file paths as extra vars
extra_vars = {
    "ssh_private_key_file": ssh_key_path,
    "tls_cert_file": cert_path
}

# Playbook usage:
# - name: Copy file using SSH
#   copy:
#     src: source.txt
#     dest: /remote/path/
#   delegate_to: remote_host
#   vars:
#     ansible_ssh_private_key_file: "{{ ssh_private_key_file }}"
```

**Cleanup**:
```python
# After execution completes
import shutil
shutil.rmtree(temp_dir, ignore_errors=True)
```

**Security**:
- ✓ Temporary directory permissions: 0700 (only owner can access)
- ✓ File permissions: 0600 (only owner can read/write)
- ✓ Files deleted immediately after execution
- ✓ Directory path is random (e.g., `/tmp/nexusguard_ansible_a8f3d9e1/`)

---

#### Method 3: Ansible Extra Variables (2130)
**Use Case**: Structured data, multiple related secrets

```python
# Build structured credential object
extra_vars = {
    **request.parameters,  # User parameters
    "db_config": {
        "host": credentials["DB_HOST"],
        "port": int(credentials["DB_PORT"]),
        "user": credentials["DB_USER"],
        "password": credentials["DB_PASSWORD"],
        "database": credentials["DB_NAME"]
    },
    "redis_config": {
        "host": credentials["REDIS_HOST"],
        "port": 6379,
        "password": credentials["REDIS_PASSWORD"]
    }
}

# Pass as JSON to ansible-playbook
cmd = [
    "ansible-playbook",
    playbook_path,
    "-e", json.dumps(extra_vars)
]

# Playbook usage:
# - name: Connect to database
#   postgresql_db:
#     login_host: "{{ db_config.host }}"
#     login_user: "{{ db_config.user }}"
#     login_password: "{{ db_config.password }}"
#     name: "{{ db_config.database }}"
```

**Security**:
- ✓ Credentials passed as in-memory JSON
- ✓ Not visible in process list (subprocess hides JSON content)
- ✓ Ansible redacts passwords in output logs
- ⚠ Visible in Ansible verbose mode (-vvv) - use carefully

---

### Ansible Execution (2200)

#### Command Construction (2210)
```python
cmd = [
    "ansible-playbook",
    f"/app/ansible/playbooks/{playbook.category}/{playbook.id}.yml",
    "-i", "/app/ansible/inventory/hosts",
    "-e", json.dumps(extra_vars),
    "--limit", ",".join(request.target_hosts)
]

if request.dry_run:
    cmd.append("--check")  # Dry-run mode (no changes)
```

#### Subprocess Execution (2220)
```python
import asyncio

# Create subprocess with credentials
process = await asyncio.create_subprocess_exec(
    *cmd,
    env=execution_env,  # Environment with credentials
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    cwd="/app"
)

# Update execution record
execution.status = PlaybookExecutionStatus.RUNNING
execution.started_at = datetime.utcnow()
await db_save(execution)

# Stream output in real-time
stdout_buffer = []
async for line in process.stdout:
    decoded_line = line.decode('utf-8')
    stdout_buffer.append(decoded_line)
    # Optional: WebSocket push to frontend for live streaming
    await websocket.send_json({"type": "output", "line": decoded_line})

# Wait for completion
await process.wait()

# Finalize execution record
execution.output = "".join(stdout_buffer)
execution.error = (await process.stderr.read()).decode('utf-8')
execution.exit_code = process.returncode
execution.status = (
    PlaybookExecutionStatus.SUCCESS if process.returncode == 0
    else PlaybookExecutionStatus.FAILED
)
execution.completed_at = datetime.utcnow()
await db_save(execution)
```

#### Cleanup (2230)
```python
# Remove temporary files (if inject_as="file")
if temp_dir and os.path.exists(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)

# Credentials are now completely removed from system
# - Not in memory (process exited)
# - Not on disk (temp files deleted)
# - Not in logs (Ansible redacts sensitive vars)
# - Not in process list (subprocess ended)
```

---

### Security Guarantees (2300)

#### Guarantee 1: No Credential Exposure (2310)

| Location | Exposure Risk | Mitigation |
|----------|--------------|------------|
| **Git Repository** | ❌ None | Credentials never in playbook YAML files |
| **Process List (`ps aux`)** | ❌ None | Only playbook path visible, not env vars |
| **Execution Logs** | ❌ None | Ansible `no_log: true` redacts passwords |
| **API Requests** | ❌ None | Credentials not in request body |
| **API Responses** | ❌ None | Credentials not in response JSON |
| **Disk Files** | ❌ None | Temp files deleted after execution |
| **Other Users** | ❌ None | Temp files have 0600 permissions |

#### Guarantee 2: Complete Audit Trail (2320)

**Vault Server Audit Log** (in Vault)
```json
{
  "time": "2024-01-20T15:30:45Z",
  "type": "response",
  "auth": {
    "display_name": "approle-nexusguard-app",
    "policies": ["nexusguard-ansible"]
  },
  "request": {
    "operation": "read",
    "path": "secret/data/nexusguard/database"
  },
  "response": {
    "data": {"*": "*"}  # Redacted in Vault audit log
  }
}
```

**Application Audit Log** (in PostgreSQL)
```sql
SELECT * FROM vault_audit_logs
WHERE playbook_execution_id = 'exec-20240120-1530';

-- Result:
-- id: audit-20240120-153045
-- operation: read_secret
-- path: secret/data/nexusguard/database
-- user: engineer@nexusguard.io
-- playbook_execution_id: exec-20240120-1530
-- timestamp: 2024-01-20 15:30:45
-- success: true
-- client_ip: 10.10.5.42
```

#### Guarantee 3: Dynamic Credentials (2330)

For dynamic secret engines (SSH, AWS, Database):

```
Timeline:
T0 (15:30:00) - Playbook execution request received
T1 (15:30:05) - Vault generates temporary SSH credentials (TTL: 1 hour)
T2 (15:30:10) - Credentials injected into playbook
T3 (15:40:25) - Playbook completes (10m 15s elapsed)
T4 (16:30:05) - Credentials automatically revoked by Vault (1 hour after T1)

Security Benefit:
- Credentials valid only for 1 hour
- Even if compromised during execution, expire quickly
- Vault automatically revokes (no manual cleanup needed)
```

#### Guarantee 4: Least Privilege (2340)

Each playbook integration specifies **minimum required secrets**:

| Playbook | Required Secrets | Denied Access |
|----------|-----------------|---------------|
| `database_failover` | `secret/data/nexusguard/database` | ❌ AWS, Redis, SSH |
| `ssl_certificate_check` | `pki/issue/nexusguard` | ❌ Database, AWS |
| `network_device_recovery` | `ssh/creds/nexusguard-ansible` | ❌ Database, PKI |
| `blockchain_node_recovery` | `secret/data/nexusguard/blockchain` | ❌ Database, AWS |

**Enforcement**:
- Vault policies restrict access per AppRole
- Each playbook executes with unique AppRole token
- Policy violation raises `VaultPermissionDenied` exception
