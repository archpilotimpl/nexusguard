# Figure 1: System Architecture Overview

```mermaid
graph TB
    subgraph "Frontend Layer (100)"
        Dashboard[Dashboard Module 110<br/>Real-time Metrics]
        Incidents[Incident Management 120<br/>Lifecycle Tracking]
        Playbooks[Playbook Library 130<br/>Execution Interface]
        Compliance[Compliance Dashboard 140<br/>Framework Scores]
        VaultUI[Vault Management 150<br/>Secret Configuration]
    end

    subgraph "Backend API Layer (200)"
        Auth[Authentication Service 210<br/>JWT & RBAC]
        Metrics[Metrics Service 220<br/>PromQL Queries]
        IncidentSvc[Incident Service 230<br/>CRUD & Lifecycle]
        Ansible[Ansible Service 240<br/>Playbook Execution]
        ComplianceSvc[Compliance Service 250<br/>Weighted Scoring]
        VaultSvc[Vault Service 260<br/>Credential Injection]
        Health[Health Service 270<br/>System Status]
    end

    subgraph "Data Storage Layer (300)"
        PostgreSQL[(PostgreSQL 310<br/>Relational Data)]
        Redis[(Redis 320<br/>Cache & Sessions)]
        Prometheus[(Prometheus 330<br/>Time-Series Metrics)]
    end

    subgraph "Monitoring & Alerting Layer (400)"
        PromServer[Prometheus Server 410<br/>Metric Collection]
        AlertMgr[Alertmanager 420<br/>Alert Routing]
        PushGW[Pushgateway 430<br/>Metric Ingestion]
        Grafana[Grafana 440<br/>Visualization]
    end

    subgraph "Security & Secrets Layer (500)"
        VaultServer[Vault Server 510<br/>Secret Management]
        SecretEngines[Secret Engines 520<br/>KV, SSH, PKI, AWS]
        Policies[Policy Management 530<br/>Access Control]
    end

    subgraph "AI & Automation Layer (600)"
        CrewAI[CrewAI Multi-Agent 610<br/>Anomaly Detection]
        AnsibleExec[Ansible Engine 620<br/>Playbook Execution]
        LearnedRepo[Learned Playbook Repo 630<br/>AI-Generated Solutions]
    end

    %% Frontend to Backend
    Dashboard --> Metrics
    Incidents --> IncidentSvc
    Playbooks --> Ansible
    Compliance --> ComplianceSvc
    VaultUI --> VaultSvc

    %% Backend to Storage
    IncidentSvc --> PostgreSQL
    ComplianceSvc --> PostgreSQL
    Ansible --> PostgreSQL
    Metrics --> Prometheus
    Auth --> Redis
    VaultSvc --> PostgreSQL

    %% Monitoring Flow
    PushGW --> PromServer
    PromServer --> Prometheus
    PromServer --> AlertMgr
    AlertMgr --> IncidentSvc
    PromServer --> Grafana

    %% AI Flow
    IncidentSvc --> CrewAI
    CrewAI --> LearnedRepo
    CrewAI --> Ansible
    Ansible --> AnsibleExec

    %% Vault Integration
    Ansible --> VaultSvc
    VaultSvc --> VaultServer
    VaultServer --> SecretEngines
    Policies --> VaultServer
    VaultSvc --> AnsibleExec

    %% Backend Auth
    Auth --> Dashboard
    Auth --> Incidents
    Auth --> Playbooks

    style Dashboard fill:#e1f5ff
    style Incidents fill:#e1f5ff
    style Playbooks fill:#e1f5ff
    style Compliance fill:#e1f5ff
    style VaultUI fill:#e1f5ff

    style Auth fill:#fff4e1
    style Metrics fill:#fff4e1
    style IncidentSvc fill:#fff4e1
    style Ansible fill:#fff4e1
    style ComplianceSvc fill:#fff4e1
    style VaultSvc fill:#fff4e1
    style Health fill:#fff4e1

    style PostgreSQL fill:#f0e1ff
    style Redis fill:#f0e1ff
    style Prometheus fill:#f0e1ff

    style PromServer fill:#e1ffe1
    style AlertMgr fill:#e1ffe1
    style PushGW fill:#e1ffe1
    style Grafana fill:#e1ffe1

    style VaultServer fill:#ffe1e1
    style SecretEngines fill:#ffe1e1
    style Policies fill:#ffe1e1

    style CrewAI fill:#ffe1f5
    style AnsibleExec fill:#ffe1f5
    style LearnedRepo fill:#ffe1f5
```

## Component Descriptions

### Frontend Layer (100)
- **Dashboard Module (110)**: React-based UI displaying real-time metrics, regional breakdown, and top incidents
- **Incident Management (120)**: Interface for incident creation, assignment, acknowledgment, and resolution
- **Playbook Library (130)**: Categorized playbook listing with execution history and dry-run capabilities
- **Compliance Dashboard (140)**: Framework scores, control-level details, and remediation recommendations
- **Vault Management (150)**: Secret path configuration, Ansible integrations, and policy viewer

### Backend API Layer (200)
- **Authentication Service (210)**: JWT token issuance, refresh, RBAC enforcement
- **Metrics Service (220)**: PromQL query generation, regional filtering, metric aggregation
- **Incident Service (230)**: CRUD operations, lifecycle management, playbook linking
- **Ansible Service (240)**: Playbook discovery, execution orchestration, Vault integration
- **Compliance Service (250)**: Severity-weighted scoring, automated evaluation, audit logging
- **Vault Service (260)**: Secret retrieval, credential injection, access auditing
- **Health Service (270)**: Component health checks (Prometheus, PostgreSQL, Redis, Vault)

### Data Storage Layer (300)
- **PostgreSQL (310)**: Incidents, compliance controls, playbook executions, audit logs
- **Redis (320)**: Session cache, real-time incident status, metric lookups
- **Prometheus (330)**: 90-day metric retention, 15-second resolution, PromQL queries

### Monitoring & Alerting Layer (400)
- **Prometheus Server (410)**: Metric scraping, alert rule evaluation, time-series storage
- **Alertmanager (420)**: Alert grouping, deduplication, webhook delivery to Incident Service
- **Pushgateway (430)**: Batch job metrics, test data ingestion, external source integration
- **Grafana (440)**: Interactive dashboards, embedded visualizations, alert history

### Security & Secrets Layer (500)
- **Vault Server (510)**: HashiCorp Vault in production mode with TLS
- **Secret Engines (520)**: KV v2, SSH, PKI, AWS, Transit, Database engines
- **Policy Management (530)**: Three role-based policies (ansible, app, admin)

### AI & Automation Layer (600)
- **CrewAI Multi-Agent (610)**: Three agents (Anomaly Detector, Playbook Matcher, LLM Consultant)
- **Ansible Engine (620)**: Playbook execution with credential injection, output capture
- **Learned Playbook Repository (630)**: Persistent storage for AI-generated playbooks with metadata
