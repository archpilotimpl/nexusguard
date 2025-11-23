# NexusGuard NOC

Network Operations Center monitoring and incident management platform for high-volume transaction processing across global regions.

## Overview

NexusGuard NOC is designed to monitor 30-50 million transactions per month across India, China, and USA regions. It provides real-time monitoring, intelligent incident detection, automated remediation through Ansible playbooks, compliance tracking for GENIUS Act 2025 and PCI-DSS v4.0, and secure credential management via HashiCorp Vault.

## Architecture

```mermaid
graph TB
    subgraph Frontend
        UI[Next.js UI<br/>Port 3090]
    end

    subgraph Backend
        API[FastAPI<br/>Port 8090]
    end

    subgraph Databases
        PG[(PostgreSQL)]
        RD[(Redis)]
    end

    subgraph Monitoring
        PROM[Prometheus<br/>Port 9090]
        GRAF[Grafana<br/>Port 3001]
        ALERT[Alertmanager<br/>Port 9093]
        PUSH[Pushgateway<br/>Port 9091]
    end

    subgraph Security
        VAULT[HashiCorp Vault<br/>Port 8200]
    end

    subgraph AI
        CREW[CrewAI Agents]
        CLAUDE[Claude Sonnet 4.5]
    end

    UI --> API
    API --> PG
    API --> RD
    API --> PROM
    PUSH --> PROM
    PROM --> GRAF
    PROM --> ALERT
    API --> VAULT
    CREW --> CLAUDE
    CREW --> API
```

## Sequence Diagrams

### 1. User Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend

    User->>Frontend: Enter credentials
    Frontend->>Backend: POST /auth/login
    Backend->>Backend: Validate credentials
    Backend->>Backend: Generate JWT tokens
    Backend-->>Frontend: {access_token, refresh_token}
    Frontend->>Frontend: Store tokens in localStorage
    Frontend-->>User: Redirect to Dashboard
```

### 2. Metrics Data Flow (Prometheus → NexusGuard)

```mermaid
sequenceDiagram
    participant TxnData as Txn Data
    participant Push as Pushgateway
    participant Prom as Prometheus
    participant API as Backend API
    participant UI as Frontend

    TxnData->>Push: Push metrics
    Prom->>Push: Scrape /metrics
    Push-->>Prom: Return metrics
    Prom->>Prom: Store in TSDB

    UI->>API: GET /metrics/summary
    API->>Prom: Query PromQL
    Prom-->>API: Time series data
    API->>API: Transform to NexusGuard format
    API-->>UI: MetricsSummary JSON
    UI->>UI: Render dashboard
```

### 3. Incident Detection and Remediation Flow

```mermaid
sequenceDiagram
    participant Prom as Prometheus
    participant API as Backend
    participant AI as CrewAI Agent
    participant Vault as Vault Service
    participant Ansible as Ansible Executor

    Prom->>API: Alert fired (webhook)
    API->>API: Create incident
    API->>AI: Analyze anomaly
    AI->>AI: Match playbook
    AI-->>API: Playbook ID

    API->>Vault: Get credentials for playbook
    Vault-->>API: {DB_PASSWORD, API_KEY, ...}

    API->>Ansible: Execute playbook with credentials
    Ansible->>Ansible: Run remediation
    Ansible-->>API: Execution result
    API->>API: Update incident status
```

### 4. Compliance Monitoring Flow

```mermaid
sequenceDiagram
    participant UI as Frontend
    participant API as Backend API
    participant Comp as Compliance Service
    participant Prom as Prometheus

    UI->>API: GET /compliance/summary
    API->>Prom: Query compliance metrics
    Prom-->>API: Metric values
    API->>Comp: Evaluate controls

    Comp->>Comp: Check GENIUS Act controls
    Comp->>Comp: Check PCI-DSS controls
    Comp->>Comp: Calculate weighted scores

    Comp-->>API: Framework status & scores
    API-->>UI: ComplianceSummary JSON
    UI->>UI: Render compliance dashboard
```

### 5. Vault Credential Retrieval for Ansible Playbooks

```mermaid
sequenceDiagram
    participant Eng as NOC Engineer
    participant API as Backend API
    participant Vault as Vault Service
    participant Ansible as Ansible Executor

    Eng->>API: Run playbook (playbook_id)
    API->>Vault: Get integration config
    Vault-->>API: {secret_paths, env_vars}

    API->>Vault: Fetch secrets from paths
    Vault->>Vault: Retrieve from KV/SSH/PKI engine
    Vault-->>API: Credentials

    API->>Ansible: Execute with injected credentials
    Ansible->>Ansible: Run playbook tasks
    Ansible-->>API: Execution result
    API-->>Eng: Status & output
```

### 6. AI Agent Anomaly Detection and Learning

```mermaid
sequenceDiagram
    participant Data as Txn Data
    participant Detect as Anomaly Detector
    participant Match as Playbook Matcher
    participant LLM as Claude Sonnet
    participant Learn as Learned Playbooks

    Data->>Detect: Load transaction data
    Detect->>Detect: Analyze for anomalies
    Detect->>Match: Detected anomalies

    Match->>Match: Search existing playbooks

    alt Playbook found
        Match-->>Detect: Playbook recommendation
    else No playbook match
        Match->>LLM: Consult for solution
        LLM->>LLM: Generate remediation steps
        LLM-->>Match: Solution JSON
        Match->>Learn: Save as new playbook
        Learn-->>Match: Playbook saved
    end
```

### 7. Complete System Data Flow

```mermaid
flowchart LR
    subgraph DataSources[Data Sources]
        TD[Data JSON]
        APP[Application Metrics]
        INFRA[Infrastructure Metrics]
        LOG[Network Infrastructure Logs]
    end

    subgraph Ingestion[Ingestion Layer]
        PG[Pushgateway]
    end

    subgraph Storage[Storage Layer]
        PROM[(Prometheus TSDB)]
        PGS[(PostgreSQL)]
        RED[(Redis Cache)]
    end

    subgraph Processing[Processing Layer]
        API[FastAPI Backend]
        COMP[Compliance Service]
        INC[Incident Service]
        VAULT[Vault Service]
    end

    subgraph Presentation[Presentation Layer]
        UI[Next.js Frontend]
        GRAF[Grafana Dashboards]
    end

    TD --> PG
    APP --> PG
    INFRA --> PG
    PG --> PROM

    PROM --> API
    API --> COMP
    API --> INC
    API --> VAULT

    API --> PGS
    API --> RED

    API --> UI
    PROM --> GRAF
    GRAF --> UI
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Starting the Application

```bash
# Start all services
./start.sh

# Start with AI Monitoring Agent
./start.sh --with-monitoring
```

### Stopping the Application

```bash
# Stop all services
./stop.sh

# Stop and remove volumes
./stop.sh --volumes

# Complete cleanup
./stop.sh --clean
```

### Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3090 | See below |
| Backend API | http://localhost:8090 | - |
| API Docs | http://localhost:8090/docs | - |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3001 | admin/admin123 |
| Alertmanager | http://localhost:9093 | - |

### Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@nexusguard.io | admin123 |
| NOC Engineer | engineer@nexusguard.io | engineer123 |
| Viewer | viewer@nexusguard.io | viewer123 |

## Features

### Dashboard
- Real-time transaction metrics across regions
- Infrastructure health monitoring
- Network layer visibility (L3, L4, L7)
- Active incident overview

### Incidents
- Automated incident creation from alerts
- Severity-based prioritization
- Root cause hypothesis
- Recommended playbooks

### Metrics
- Embedded Grafana dashboards
- Transaction success/failure rates
- Latency percentiles (P50, P95, P99)
- Infrastructure resource utilization

### Playbooks
- Ansible playbook library
- Vault integration for credentials
- Execution history
- Dry-run support

### Compliance
- GENIUS Act 2025 tracking
- PCI-DSS v4.0 compliance
- Automated control checks
- Audit logs

### Vault
- HashiCorp Vault integration
- Secure credential management
- Ansible playbook credential injection
- Policy management

## Data Flow: Prometheus → NexusGuard

All test data in `prometheus/test_data/` flows through the system:

1. **Test Data Files**:
   - `transactions_normal.json` - Baseline metrics
   - `transactions_abnormal.json` - Degraded performance
   - `transactions_anomaly.json` - Critical issues
   - `compliance_metrics.json` - Compliance checks

2. **Data Pipeline**:
   ```
   Test Data → Pushgateway → Prometheus → Backend API → Frontend
   ```

3. **Compliance Checks**: The `compliance_metrics.json` contains automated checks that evaluate:
   - GENIUS Act: Reserve ratios, KYC rates, redemption times
   - PCI-DSS: Encryption, MFA, patching, training

## Project Structure

```
NexusGuardNOC/
├── backend/
│   ├── app/
│   │   ├── api/           # REST endpoints
│   │   ├── core/          # Config, security
│   │   ├── models/        # Pydantic schemas
│   │   └── services/      # Business logic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   ├── lib/           # API client
│   │   └── types/         # TypeScript types
│   └── package.json
├── agents/
│   ├── noc_monitoring_crew.py
│   └── learned_playbooks/
├── ansible/
│   ├── playbooks/
│   └── inventory/
├── prometheus/
│   ├── prometheus.yml
│   ├── rules/
│   └── test_data/         # Metrics data
├── grafana/
│   └── provisioning/
├── docker-compose.yml
├── start.sh
└── stop.sh
```

## API Endpoints

### Core Endpoints
- `POST /api/v1/auth/login` - Authenticate
- `GET /api/v1/metrics/summary` - Metrics
- `GET /api/v1/incidents` - Incidents
- `GET /api/v1/ansible/playbooks` - Playbooks
- `GET /api/v1/compliance/summary` - Compliance
- `GET /api/v1/vault/summary` - Vault status

Full documentation at http://localhost:8090/docs

## Environment Variables

### Backend (.env)
```bash
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@postgres/nexusguard
REDIS_URL=redis://redis:6379
PROMETHEUS_URL=http://prometheus:9090
VAULT_ADDR=http://vault:8200
```

### Agent (.env)
```bash
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

## Troubleshooting

### Docker Network Issues
```bash
docker compose down --remove-orphans
docker network prune -f
./start.sh
```

### Grafana Not Showing Data
1. Check datasource UID matches "prometheus"
2. Verify pushgateway scrape job
3. Reset: `docker volume rm nexusguardnoc_grafana_data`

## License

Copyright 2025 Archpilot. All rights reserved.

---

Powered by **Archpilot**
