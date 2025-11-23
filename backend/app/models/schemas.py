"""Pydantic schemas for request/response validation."""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# Enums
class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class PlaybookExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# Authentication Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: str = "viewer"
    region: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class User(UserBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    role: str
    region: Optional[str] = None


# Metrics Schemas
class TransactionMetrics(BaseModel):
    """Transaction-related metrics."""
    total_count: int = Field(..., description="Total transaction count")
    success_count: int = Field(..., description="Successful transactions")
    failure_count: int = Field(..., description="Failed transactions")
    success_rate: float = Field(..., description="Success rate percentage")
    error_rate: float = Field(..., description="Error rate percentage")
    avg_latency_ms: float = Field(..., description="Average latency in milliseconds")
    p50_latency_ms: float = Field(..., description="50th percentile latency")
    p95_latency_ms: float = Field(..., description="95th percentile latency")
    p99_latency_ms: float = Field(..., description="99th percentile latency")
    transactions_per_second: float = Field(..., description="TPS")
    hash_mismatch_count: int = Field(0, description="Blockchain hash mismatches")
    blockchain_failures: int = Field(0, description="Blockchain commit failures")


class FirewallMetrics(BaseModel):
    """Firewall-specific metrics."""
    total_firewalls: int = Field(0, description="Total firewall devices")
    firewalls_up: int = Field(0, description="Active firewalls")
    accepts_per_second: float = Field(0, description="Accepted connections/sec")
    denies_per_second: float = Field(0, description="Denied connections/sec")
    total_accepts: int = Field(0, description="Total accepted connections")
    total_denies: int = Field(0, description="Total denied connections")
    deny_rate: float = Field(0, description="Deny rate percentage")
    sessions_active: int = Field(0, description="Active firewall sessions")
    sessions_max: int = Field(0, description="Maximum firewall sessions")
    cpu_usage: float = Field(0, description="Average firewall CPU %")
    memory_usage: float = Field(0, description="Average firewall memory %")
    throughput_mbps: float = Field(0, description="Throughput in Mbps")
    blocked_threats: int = Field(0, description="Blocked security threats")
    vpn_tunnels_active: int = Field(0, description="Active VPN tunnels")


class Layer3Metrics(BaseModel):
    """Layer 3 (Network Layer) router metrics."""
    total_routers: int = Field(0, description="Total routers")
    routers_up: int = Field(0, description="Active routers")
    bgp_sessions_total: int = Field(0, description="Total BGP sessions")
    bgp_sessions_established: int = Field(0, description="Established BGP sessions")
    ospf_neighbors_total: int = Field(0, description="Total OSPF neighbors")
    ospf_neighbors_full: int = Field(0, description="Full OSPF neighbors")
    routes_total: int = Field(0, description="Total routes in routing table")
    routes_bgp: int = Field(0, description="BGP routes")
    routes_ospf: int = Field(0, description="OSPF routes")
    routes_static: int = Field(0, description="Static routes")
    packets_forwarded: int = Field(0, description="Total packets forwarded")
    packets_dropped: int = Field(0, description="Total packets dropped")
    cpu_usage: float = Field(0, description="Average router CPU %")
    memory_usage: float = Field(0, description="Average router memory %")


class Layer4Metrics(BaseModel):
    """Layer 4 (Transport Layer) load balancer and switch metrics."""
    total_load_balancers: int = Field(0, description="Total load balancers")
    load_balancers_up: int = Field(0, description="Active load balancers")
    active_connections: int = Field(0, description="Active L4 connections")
    connections_per_second: float = Field(0, description="New connections/sec")
    total_bandwidth_mbps: float = Field(0, description="Total bandwidth Mbps")
    ssl_tps: float = Field(0, description="SSL transactions/sec")
    ssl_handshakes: int = Field(0, description="SSL handshakes completed")
    backend_servers_total: int = Field(0, description="Total backend servers")
    backend_servers_healthy: int = Field(0, description="Healthy backend servers")
    health_check_failures: int = Field(0, description="Backend health check failures")
    session_persistence_hits: int = Field(0, description="Session persistence hits")
    cpu_usage: float = Field(0, description="Average load balancer CPU %")
    memory_usage: float = Field(0, description="Average load balancer memory %")


class NetworkMetrics(BaseModel):
    """Comprehensive network device metrics."""
    # Overall metrics
    devices_total: int = Field(..., description="Total network devices")
    devices_up: int = Field(..., description="Devices online")
    devices_down: int = Field(..., description="Devices offline")
    avg_interface_utilization: float = Field(..., description="Average interface utilization %")
    total_errors: int = Field(..., description="Total interface errors")
    total_drops: int = Field(..., description="Total packet drops")
    firewall_accepts: int = Field(..., description="Firewall accepted connections")
    firewall_denies: int = Field(..., description="Firewall denied connections")

    # Detailed layer-specific metrics
    firewall: Optional[FirewallMetrics] = Field(None, description="Firewall metrics")
    layer3: Optional[Layer3Metrics] = Field(None, description="Layer 3 router metrics")
    layer4: Optional[Layer4Metrics] = Field(None, description="Layer 4 load balancer metrics")


class InfrastructureMetrics(BaseModel):
    """Infrastructure metrics for servers and databases."""
    avg_cpu_usage: float = Field(..., description="Average CPU usage %")
    avg_memory_usage: float = Field(..., description="Average memory usage %")
    avg_disk_usage: float = Field(..., description="Average disk usage %")
    total_servers: int = Field(..., description="Total servers monitored")
    healthy_servers: int = Field(..., description="Healthy servers count")
    db_connections_active: int = Field(..., description="Active DB connections")
    db_connections_max: int = Field(..., description="Max DB connections")
    db_avg_query_latency_ms: float = Field(..., description="Average query latency")
    db_replication_lag_ms: float = Field(0, description="Replication lag")


class RegionMetrics(BaseModel):
    """Metrics for a specific region."""
    region: str = Field(..., description="Region name (india, china, usa)")
    transactions: TransactionMetrics
    network: NetworkMetrics
    infrastructure: InfrastructureMetrics
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetricsSummary(BaseModel):
    """Aggregated metrics summary across all regions."""
    global_transactions: TransactionMetrics
    global_network: NetworkMetrics
    global_infrastructure: InfrastructureMetrics
    regions: List[RegionMetrics]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Incident Schemas
class IncidentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str
    severity: IncidentSeverity
    region: str
    service: str
    root_cause_hypothesis: Optional[str] = None
    corrective_actions: Optional[List[str]] = None
    recommended_playbook: Optional[str] = None
    labels: Optional[Dict[str, str]] = None


class IncidentCreate(IncidentBase):
    alert_fingerprint: Optional[str] = None


class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    severity: Optional[IncidentSeverity] = None
    root_cause_hypothesis: Optional[str] = None
    corrective_actions: Optional[List[str]] = None
    resolution_notes: Optional[str] = None
    assigned_to: Optional[str] = None


class Incident(IncidentBase):
    id: str
    status: IncidentStatus = IncidentStatus.OPEN
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    alert_fingerprint: Optional[str] = None
    related_incidents: Optional[List[str]] = None
    playbook_executions: Optional[List[str]] = None

    class Config:
        from_attributes = True


# Ansible Playbook Schemas
class PlaybookParameter(BaseModel):
    name: str
    description: str
    type: str = "string"
    required: bool = False
    default: Optional[Any] = None


class PlaybookStep(BaseModel):
    order: int
    name: str
    description: str
    is_destructive: bool = False


class Playbook(BaseModel):
    id: str
    name: str
    description: str
    category: str = Field(..., description="e.g., application, network, infrastructure")
    incident_types: List[str] = Field(..., description="Incident types this playbook addresses")
    parameters: List[PlaybookParameter] = []
    steps: List[PlaybookStep] = Field(default=[], description="Execution steps")
    preconditions: Optional[List[str]] = None
    safety_checks: Optional[List[str]] = None
    estimated_duration_minutes: int = 5
    requires_approval: bool = False
    is_automated: bool = False
    rollback_playbook: Optional[str] = None
    file_path: str


class PlaybookExecutionRequest(BaseModel):
    playbook_id: str
    incident_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    target_hosts: Optional[List[str]] = None
    dry_run: bool = False


class PlaybookExecution(BaseModel):
    id: str
    playbook_id: str
    incident_id: Optional[str] = None
    status: PlaybookExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    executed_by: str
    parameters: Dict[str, Any] = {}
    target_hosts: List[str] = []
    output: Optional[str] = None
    error: Optional[str] = None
    dry_run: bool = False

    class Config:
        from_attributes = True


# Health Check Schemas
class ServiceHealth(BaseModel):
    name: str
    status: HealthStatus
    region: Optional[str] = None
    latency_ms: Optional[float] = None
    last_check: datetime
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SystemHealth(BaseModel):
    status: HealthStatus
    services: List[ServiceHealth]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Alert Rule Schemas
class AlertRule(BaseModel):
    id: str
    name: str
    expression: str = Field(..., description="PromQL expression")
    for_duration: str = Field("5m", description="Duration before firing")
    severity: IncidentSeverity
    description: str
    summary: str
    runbook_url: Optional[str] = None
    labels: Dict[str, str] = {}
    annotations: Dict[str, str] = {}
    is_active: bool = True


# Anomaly Detection Schemas
class AnomalyDetection(BaseModel):
    id: str
    metric_name: str
    region: str
    detected_at: datetime
    anomaly_type: str = Field(..., description="spike, drop, trend_change, etc.")
    expected_value: float
    actual_value: float
    deviation_percentage: float
    confidence: float = Field(..., ge=0, le=1)
    description: str
    related_metrics: Optional[List[str]] = None


# SLO Schemas
class SLODefinition(BaseModel):
    id: str
    name: str
    description: str
    target_percentage: float = Field(..., ge=0, le=100)
    window_days: int = 30
    metric_query: str
    error_budget_remaining: Optional[float] = None


class SLOStatus(BaseModel):
    slo: SLODefinition
    current_value: float
    target_value: float
    is_meeting_target: bool
    error_budget_consumed: float
    burn_rate: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
