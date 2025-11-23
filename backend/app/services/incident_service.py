"""Incident management service."""
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from app.core.logging import get_logger
from app.models.schemas import (
    Incident,
    IncidentCreate,
    IncidentUpdate,
    IncidentStatus,
    IncidentSeverity,
)

logger = get_logger(__name__)


class IncidentService:
    """Service for managing incidents."""

    def __init__(self):
        # In-memory storage (replace with database in production)
        self._incidents: Dict[str, Incident] = {}
        self._init_sample_incidents()

    def _init_sample_incidents(self):
        """Initialize with sample incidents for demo."""
        sample_incidents = [
            {
                "id": "inc-001",
                "title": "High Error Rate in India Region",
                "description": "Transaction error rate has exceeded 5% threshold in the India region for the past 15 minutes.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.OPEN,
                "region": "india",
                "service": "payment-gateway",
                "root_cause_hypothesis": "Possible database connection pool exhaustion or network latency spike.",
                "corrective_actions": [
                    "Check database connection pool metrics",
                    "Verify network connectivity to database cluster",
                    "Review recent deployments for configuration changes",
                    "Consider scaling database connections if needed"
                ],
                "recommended_playbook": "high_error_rate_investigation",
                "created_at": datetime.utcnow(),
                "labels": {"team": "payments", "priority": "p1"}
            },
            {
                "id": "inc-002",
                "title": "Network Device Unreachable - US-EAST-FW-01",
                "description": "Firewall device US-EAST-FW-01 is not responding to health checks.",
                "severity": IncidentSeverity.CRITICAL,
                "status": IncidentStatus.IN_PROGRESS,
                "region": "usa",
                "service": "network-infrastructure",
                "root_cause_hypothesis": "Hardware failure or network path issue to management interface.",
                "corrective_actions": [
                    "Verify physical connectivity and power status",
                    "Check out-of-band management access",
                    "Review recent configuration changes",
                    "Prepare failover to secondary firewall"
                ],
                "recommended_playbook": "network_device_recovery",
                "created_at": datetime.utcnow(),
                "assigned_to": "noc-engineer-1",
                "labels": {"team": "network", "priority": "p0"}
            },
            {
                "id": "inc-003",
                "title": "Blockchain Commit Failures - China Region",
                "description": "Multiple blockchain commit failures detected in the past hour.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.ACKNOWLEDGED,
                "region": "china",
                "service": "blockchain-ledger",
                "root_cause_hypothesis": "Consensus node synchronization issues or network partition.",
                "corrective_actions": [
                    "Check blockchain node health and sync status",
                    "Verify network connectivity between nodes",
                    "Review transaction queue depth",
                    "Consider restarting lagging nodes"
                ],
                "recommended_playbook": "blockchain_node_recovery",
                "created_at": datetime.utcnow(),
                "acknowledged_at": datetime.utcnow(),
                "labels": {"team": "blockchain", "priority": "p1"}
            },
            {
                "id": "inc-004",
                "title": "Database Replication Lag Critical - USA Region",
                "description": "Primary-replica replication lag has exceeded 30 seconds. Data consistency at risk.",
                "severity": IncidentSeverity.CRITICAL,
                "status": IncidentStatus.OPEN,
                "region": "usa",
                "service": "postgresql-cluster",
                "root_cause_hypothesis": "Heavy write load or network bottleneck between primary and replica.",
                "corrective_actions": [
                    "Check current write QPS on primary",
                    "Verify network throughput between nodes",
                    "Review long-running queries",
                    "Consider promoting replica if primary fails"
                ],
                "recommended_playbook": "database_failover",
                "created_at": datetime.utcnow(),
                "labels": {"team": "database", "priority": "p0"}
            },
            {
                "id": "inc-005",
                "title": "Disk Usage Critical - App Server CN-APP-03",
                "description": "Disk usage on /var/log has exceeded 90% threshold.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.OPEN,
                "region": "china",
                "service": "application-server",
                "root_cause_hypothesis": "Log files not rotating properly or excessive error logging.",
                "corrective_actions": [
                    "Check log rotation configuration",
                    "Identify largest log files",
                    "Clean up old log archives",
                    "Investigate root cause of excessive logging"
                ],
                "recommended_playbook": "disk_cleanup",
                "created_at": datetime.utcnow(),
                "labels": {"team": "infrastructure", "priority": "p1"}
            },
            {
                "id": "inc-006",
                "title": "API Rate Limit Exceeded - Payment Service",
                "description": "Multiple clients hitting rate limits on payment API. Legitimate traffic may be affected.",
                "severity": IncidentSeverity.MEDIUM,
                "status": IncidentStatus.OPEN,
                "region": "india",
                "service": "payment-api",
                "root_cause_hypothesis": "Traffic spike from marketing campaign or misconfigured client retry logic.",
                "corrective_actions": [
                    "Review rate limit metrics by client",
                    "Identify top offending clients",
                    "Consider temporary rate limit increase",
                    "Contact clients with misconfigured retry logic"
                ],
                "recommended_playbook": "api_rate_limit_adjust",
                "created_at": datetime.utcnow(),
                "labels": {"team": "api", "priority": "p2"}
            },
            {
                "id": "inc-007",
                "title": "Memory Pressure - Redis Cache Cluster",
                "description": "Redis memory usage at 85%. Evictions starting to occur.",
                "severity": IncidentSeverity.MEDIUM,
                "status": IncidentStatus.ACKNOWLEDGED,
                "region": "usa",
                "service": "redis-cache",
                "root_cause_hypothesis": "Cache key explosion or missing TTLs on cached objects.",
                "corrective_actions": [
                    "Analyze memory usage by key pattern",
                    "Identify keys without TTL",
                    "Consider selective cache flush",
                    "Review application caching strategy"
                ],
                "recommended_playbook": "redis_cache_flush",
                "created_at": datetime.utcnow(),
                "acknowledged_at": datetime.utcnow(),
                "labels": {"team": "cache", "priority": "p2"}
            },
            {
                "id": "inc-008",
                "title": "SSL Certificate Expiring Soon - api.nexusguard.com",
                "description": "SSL certificate will expire in 7 days. Renewal required.",
                "severity": IncidentSeverity.MEDIUM,
                "status": IncidentStatus.OPEN,
                "region": "usa",
                "service": "ssl-certificates",
                "root_cause_hypothesis": "Auto-renewal failed or certificate not in rotation.",
                "corrective_actions": [
                    "Check Let's Encrypt or CA renewal status",
                    "Manually trigger certificate renewal",
                    "Verify DNS ACME challenge configuration",
                    "Update certificate in load balancer"
                ],
                "recommended_playbook": "ssl_certificate_check",
                "created_at": datetime.utcnow(),
                "labels": {"team": "security", "priority": "p2"}
            },
            {
                "id": "inc-009",
                "title": "DDoS Attack Detected - India Edge",
                "description": "Abnormal traffic pattern detected. 50x increase in requests from suspicious IP ranges.",
                "severity": IncidentSeverity.CRITICAL,
                "status": IncidentStatus.IN_PROGRESS,
                "region": "india",
                "service": "edge-firewall",
                "root_cause_hypothesis": "Distributed denial of service attack targeting API endpoints.",
                "corrective_actions": [
                    "Enable DDoS protection rules",
                    "Block suspicious IP ranges",
                    "Enable rate limiting at edge",
                    "Contact upstream provider for mitigation"
                ],
                "recommended_playbook": "firewall_emergency_block",
                "created_at": datetime.utcnow(),
                "assigned_to": "noc-engineer-2",
                "labels": {"team": "security", "priority": "p0"}
            },
            {
                "id": "inc-010",
                "title": "Kubernetes Pod CrashLoopBackOff - order-service",
                "description": "Order service pods in CrashLoopBackOff state. 5 restarts in last 10 minutes.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.OPEN,
                "region": "china",
                "service": "order-service",
                "root_cause_hypothesis": "Application startup failure due to missing config or OOM kill.",
                "corrective_actions": [
                    "Check pod logs for startup errors",
                    "Verify ConfigMap and Secret availability",
                    "Check resource limits vs actual usage",
                    "Review recent deployment changes"
                ],
                "recommended_playbook": "kubernetes_pod_restart",
                "created_at": datetime.utcnow(),
                "labels": {"team": "platform", "priority": "p1"}
            },
            {
                "id": "inc-011",
                "title": "Connection Pool Exhaustion - USA Application",
                "description": "Database connection pool at 100% utilization. New connections being rejected.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.OPEN,
                "region": "usa",
                "service": "application-server",
                "root_cause_hypothesis": "Connection leak or long-running transactions holding connections.",
                "corrective_actions": [
                    "Identify connections holding longest",
                    "Check for uncommitted transactions",
                    "Review connection timeout settings",
                    "Consider application restart to reset pool"
                ],
                "recommended_playbook": "connection_pool_reset",
                "created_at": datetime.utcnow(),
                "labels": {"team": "application", "priority": "p1"}
            },
            {
                "id": "inc-012",
                "title": "High Latency - Transaction Processing",
                "description": "P99 latency for transaction processing exceeded 2000ms (SLO: 500ms).",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.ACKNOWLEDGED,
                "region": "india",
                "service": "transaction-processor",
                "root_cause_hypothesis": "Downstream service degradation or database query performance issue.",
                "corrective_actions": [
                    "Check distributed tracing for bottlenecks",
                    "Review database query execution plans",
                    "Check downstream service health",
                    "Consider enabling circuit breaker"
                ],
                "recommended_playbook": "high_error_rate_investigation",
                "created_at": datetime.utcnow(),
                "acknowledged_at": datetime.utcnow(),
                "labels": {"team": "transactions", "priority": "p1"}
            },
            {
                "id": "inc-013",
                "title": "Load Balancer Health Check Failures",
                "description": "3 of 8 backend servers failing health checks on load balancer.",
                "severity": IncidentSeverity.MEDIUM,
                "status": IncidentStatus.OPEN,
                "region": "usa",
                "service": "haproxy-lb",
                "root_cause_hypothesis": "Application not responding on health endpoint or resource exhaustion.",
                "corrective_actions": [
                    "Check application health endpoints directly",
                    "Review server resource utilization",
                    "Check for network issues to backend",
                    "Drain and investigate failed servers"
                ],
                "recommended_playbook": "load_balancer_drain",
                "created_at": datetime.utcnow(),
                "labels": {"team": "network", "priority": "p2"}
            },
            {
                "id": "inc-014",
                "title": "Hash Mismatch Detected - Blockchain Verification",
                "description": "Transaction hash verification failed for 15 transactions in the last hour.",
                "severity": IncidentSeverity.CRITICAL,
                "status": IncidentStatus.OPEN,
                "region": "china",
                "service": "blockchain-verifier",
                "root_cause_hypothesis": "Data tampering attempt or node synchronization issue causing hash inconsistency.",
                "corrective_actions": [
                    "Isolate affected transactions for investigation",
                    "Compare hashes across multiple nodes",
                    "Check for unauthorized access attempts",
                    "Initiate blockchain integrity audit"
                ],
                "recommended_playbook": "collect_diagnostics",
                "created_at": datetime.utcnow(),
                "labels": {"team": "security", "priority": "p0"}
            },
            {
                "id": "inc-015",
                "title": "Memory Leak Detected - Auth Service",
                "description": "Memory usage growing linearly. Currently at 75% with no GC reclamation.",
                "severity": IncidentSeverity.MEDIUM,
                "status": IncidentStatus.OPEN,
                "region": "india",
                "service": "auth-service",
                "root_cause_hypothesis": "Memory leak in session handling or token cache not expiring.",
                "corrective_actions": [
                    "Capture heap dump for analysis",
                    "Review recent code changes",
                    "Schedule rolling restart before OOM",
                    "Enable memory profiling"
                ],
                "recommended_playbook": "memory_pressure_relief",
                "created_at": datetime.utcnow(),
                "labels": {"team": "auth", "priority": "p2"}
            },
            {
                "id": "inc-016",
                "title": "Network Partition Detected",
                "description": "Intermittent connectivity between USA and China datacenters.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.IN_PROGRESS,
                "region": "usa",
                "service": "wan-connectivity",
                "root_cause_hypothesis": "Submarine cable issue or routing problem at ISP level.",
                "corrective_actions": [
                    "Check BGP route advertisements",
                    "Verify VPN tunnel status",
                    "Contact network provider",
                    "Enable traffic failover through alternate path"
                ],
                "recommended_playbook": "network_connectivity_test",
                "created_at": datetime.utcnow(),
                "assigned_to": "noc-engineer-1",
                "labels": {"team": "network", "priority": "p1"}
            },
            {
                "id": "inc-017",
                "title": "Scheduled Maintenance - DB Upgrade",
                "description": "Planned PostgreSQL upgrade from 14.x to 15.x scheduled.",
                "severity": IncidentSeverity.LOW,
                "status": IncidentStatus.ACKNOWLEDGED,
                "region": "usa",
                "service": "postgresql-cluster",
                "root_cause_hypothesis": "Scheduled maintenance window.",
                "corrective_actions": [
                    "Notify stakeholders of maintenance window",
                    "Prepare rollback procedure",
                    "Drain connections before upgrade",
                    "Validate application compatibility"
                ],
                "recommended_playbook": "load_balancer_drain",
                "created_at": datetime.utcnow(),
                "acknowledged_at": datetime.utcnow(),
                "labels": {"team": "database", "priority": "p3", "type": "maintenance"}
            },
            {
                "id": "inc-018",
                "title": "Log Aggregation Pipeline Lag",
                "description": "Log ingestion lagging behind by 10 minutes. Monitoring visibility affected.",
                "severity": IncidentSeverity.MEDIUM,
                "status": IncidentStatus.OPEN,
                "region": "india",
                "service": "log-pipeline",
                "root_cause_hypothesis": "Kafka consumer group lag or Elasticsearch indexing bottleneck.",
                "corrective_actions": [
                    "Check Kafka consumer group lag",
                    "Review Elasticsearch cluster health",
                    "Scale log processors if needed",
                    "Identify log volume spike source"
                ],
                "recommended_playbook": "log_rotation_emergency",
                "created_at": datetime.utcnow(),
                "labels": {"team": "observability", "priority": "p2"}
            },
            {
                "id": "inc-019",
                "title": "Consensus Failure - Blockchain Network",
                "description": "Blockchain nodes failing to reach consensus. Transaction finality delayed.",
                "severity": IncidentSeverity.CRITICAL,
                "status": IncidentStatus.OPEN,
                "region": "china",
                "service": "blockchain-consensus",
                "root_cause_hypothesis": "Byzantine node behavior or network partition affecting quorum.",
                "corrective_actions": [
                    "Identify nodes not participating in consensus",
                    "Check network connectivity between validator nodes",
                    "Review node logs for voting failures",
                    "Consider removing faulty nodes from validator set"
                ],
                "recommended_playbook": "blockchain_node_recovery",
                "created_at": datetime.utcnow(),
                "labels": {"team": "blockchain", "priority": "p0"}
            },
            {
                "id": "inc-020",
                "title": "Kafka Broker Offline - USA Cluster",
                "description": "Kafka broker kafka-usa-03 is not responding. Topic partitions under-replicated.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.IN_PROGRESS,
                "region": "usa",
                "service": "kafka-cluster",
                "root_cause_hypothesis": "Broker crash due to disk failure or JVM OOM.",
                "corrective_actions": [
                    "Check broker logs for crash reason",
                    "Verify disk health and space",
                    "Restart broker if recoverable",
                    "Reassign partitions if broker unrecoverable"
                ],
                "recommended_playbook": "restart_application",
                "created_at": datetime.utcnow(),
                "assigned_to": "noc-engineer-1",
                "labels": {"team": "messaging", "priority": "p1"}
            },
            {
                "id": "inc-021",
                "title": "Slow DNS Resolution - India Region",
                "description": "DNS queries taking >500ms. Application timeouts increasing.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.OPEN,
                "region": "india",
                "service": "dns-resolver",
                "root_cause_hypothesis": "DNS cache poisoning attempt or upstream resolver issues.",
                "corrective_actions": [
                    "Check local DNS cache hit rate",
                    "Verify upstream resolver health",
                    "Switch to backup DNS servers",
                    "Clear DNS cache if corrupted"
                ],
                "recommended_playbook": "network_connectivity_test",
                "created_at": datetime.utcnow(),
                "labels": {"team": "network", "priority": "p1"}
            },
            {
                "id": "inc-022",
                "title": "Transaction Queue Backlog",
                "description": "Transaction processing queue depth at 50,000. Processing rate degraded.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.ACKNOWLEDGED,
                "region": "india",
                "service": "transaction-queue",
                "root_cause_hypothesis": "Consumer processing slowdown or sudden traffic spike.",
                "corrective_actions": [
                    "Scale up consumer instances",
                    "Check consumer processing latency",
                    "Identify slow processing transactions",
                    "Consider temporary rate limiting"
                ],
                "recommended_playbook": "api_rate_limit_adjust",
                "created_at": datetime.utcnow(),
                "acknowledged_at": datetime.utcnow(),
                "labels": {"team": "transactions", "priority": "p1"}
            },
            {
                "id": "inc-023",
                "title": "Storage IOPS Throttled - China DB",
                "description": "Database storage hitting IOPS limits. Query latency spiking.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.OPEN,
                "region": "china",
                "service": "database-storage",
                "root_cause_hypothesis": "Heavy batch job or inefficient queries causing excessive I/O.",
                "corrective_actions": [
                    "Identify top I/O consuming queries",
                    "Kill or optimize heavy batch jobs",
                    "Consider scaling storage tier",
                    "Enable query caching"
                ],
                "recommended_playbook": "high_error_rate_investigation",
                "created_at": datetime.utcnow(),
                "labels": {"team": "database", "priority": "p1"}
            },
            {
                "id": "inc-024",
                "title": "JWT Token Validation Failures",
                "description": "30% of JWT token validations failing. Users experiencing auth errors.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.OPEN,
                "region": "usa",
                "service": "auth-service",
                "root_cause_hypothesis": "Key rotation issue or clock skew between services.",
                "corrective_actions": [
                    "Verify JWT signing keys are synced",
                    "Check NTP synchronization across services",
                    "Review token expiry settings",
                    "Clear auth service cache"
                ],
                "recommended_playbook": "restart_application",
                "created_at": datetime.utcnow(),
                "labels": {"team": "auth", "priority": "p1"}
            },
            {
                "id": "inc-025",
                "title": "CDN Cache Miss Rate High",
                "description": "CDN cache hit rate dropped to 40%. Origin server load increasing.",
                "severity": IncidentSeverity.MEDIUM,
                "status": IncidentStatus.OPEN,
                "region": "india",
                "service": "cdn-edge",
                "root_cause_hypothesis": "Cache invalidation storm or misconfigured cache headers.",
                "corrective_actions": [
                    "Review recent cache purge operations",
                    "Check cache-control headers on responses",
                    "Verify CDN configuration",
                    "Scale origin servers if needed"
                ],
                "recommended_playbook": "collect_diagnostics",
                "created_at": datetime.utcnow(),
                "labels": {"team": "cdn", "priority": "p2"}
            },
            {
                "id": "inc-026",
                "title": "Service Mesh Sidecar Failures",
                "description": "Envoy sidecar proxies crashing in payment-service pods.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.OPEN,
                "region": "usa",
                "service": "service-mesh",
                "root_cause_hypothesis": "Memory limit too low or configuration push failure.",
                "corrective_actions": [
                    "Check Envoy sidecar logs",
                    "Verify Istio control plane health",
                    "Increase sidecar memory limits",
                    "Roll back recent mesh configuration"
                ],
                "recommended_playbook": "kubernetes_pod_restart",
                "created_at": datetime.utcnow(),
                "labels": {"team": "platform", "priority": "p1"}
            },
            {
                "id": "inc-027",
                "title": "Grafana Dashboard Unavailable",
                "description": "Grafana service returning 503. NOC monitoring visibility impacted.",
                "severity": IncidentSeverity.MEDIUM,
                "status": IncidentStatus.OPEN,
                "region": "usa",
                "service": "grafana",
                "root_cause_hypothesis": "Database connection exhaustion or memory pressure.",
                "corrective_actions": [
                    "Check Grafana pod status",
                    "Verify Grafana database connectivity",
                    "Restart Grafana service",
                    "Review dashboard query complexity"
                ],
                "recommended_playbook": "restart_application",
                "created_at": datetime.utcnow(),
                "labels": {"team": "observability", "priority": "p2"}
            },
            {
                "id": "inc-028",
                "title": "API Gateway 502 Errors",
                "description": "API Gateway returning 502 errors for 5% of requests.",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.IN_PROGRESS,
                "region": "china",
                "service": "api-gateway",
                "root_cause_hypothesis": "Backend service timeout or connection refused.",
                "corrective_actions": [
                    "Identify failing backend services",
                    "Check backend service health",
                    "Increase gateway timeout settings",
                    "Enable circuit breaker for failing backends"
                ],
                "recommended_playbook": "service_health_check",
                "created_at": datetime.utcnow(),
                "assigned_to": "noc-engineer-2",
                "labels": {"team": "api", "priority": "p1"}
            },
            {
                "id": "inc-029",
                "title": "Vault Seal Event",
                "description": "HashiCorp Vault has sealed. Secrets unavailable to applications.",
                "severity": IncidentSeverity.CRITICAL,
                "status": IncidentStatus.OPEN,
                "region": "usa",
                "service": "vault",
                "root_cause_hypothesis": "Unexpected restart or storage backend failure.",
                "corrective_actions": [
                    "Initiate vault unseal procedure",
                    "Verify storage backend health",
                    "Check for unauthorized access attempts",
                    "Notify on-call for unseal keys"
                ],
                "recommended_playbook": "collect_diagnostics",
                "created_at": datetime.utcnow(),
                "labels": {"team": "security", "priority": "p0"}
            },
            {
                "id": "inc-030",
                "title": "Prometheus Scrape Failures",
                "description": "Prometheus failing to scrape 15 targets. Metrics gaps appearing.",
                "severity": IncidentSeverity.MEDIUM,
                "status": IncidentStatus.OPEN,
                "region": "india",
                "service": "prometheus",
                "root_cause_hypothesis": "Target pods restarting or network policy blocking scrapes.",
                "corrective_actions": [
                    "Check target pod health",
                    "Verify network policies allow scraping",
                    "Check Prometheus memory usage",
                    "Increase scrape timeout if needed"
                ],
                "recommended_playbook": "network_connectivity_test",
                "created_at": datetime.utcnow(),
                "labels": {"team": "observability", "priority": "p2"}
            },
            {
                "id": "inc-031",
                "title": "Cross-Region Latency Spike",
                "description": "Latency between India and USA regions increased to 800ms (baseline: 200ms).",
                "severity": IncidentSeverity.HIGH,
                "status": IncidentStatus.OPEN,
                "region": "india",
                "service": "cross-region-link",
                "root_cause_hypothesis": "ISP routing change or congestion on undersea cable.",
                "corrective_actions": [
                    "Run traceroute to identify hop with latency",
                    "Check for ISP maintenance notices",
                    "Enable traffic routing through alternate path",
                    "Contact ISP for resolution"
                ],
                "recommended_playbook": "network_connectivity_test",
                "created_at": datetime.utcnow(),
                "labels": {"team": "network", "priority": "p1"}
            },
            {
                "id": "inc-032",
                "title": "Elasticsearch Cluster Yellow",
                "description": "Elasticsearch cluster health is yellow. Some replicas unassigned.",
                "severity": IncidentSeverity.MEDIUM,
                "status": IncidentStatus.ACKNOWLEDGED,
                "region": "china",
                "service": "elasticsearch",
                "root_cause_hypothesis": "Node disk watermark exceeded or node temporarily offline.",
                "corrective_actions": [
                    "Check cluster allocation explain",
                    "Verify node disk usage",
                    "Clear old indices if disk full",
                    "Force allocate replicas if safe"
                ],
                "recommended_playbook": "disk_cleanup",
                "created_at": datetime.utcnow(),
                "acknowledged_at": datetime.utcnow(),
                "labels": {"team": "search", "priority": "p2"}
            }
        ]

        for inc_data in sample_incidents:
            incident = Incident(**inc_data)
            self._incidents[incident.id] = incident

    async def create_incident(self, incident_data: IncidentCreate) -> Incident:
        """Create a new incident."""
        incident_id = f"inc-{uuid.uuid4().hex[:8]}"

        incident = Incident(
            id=incident_id,
            title=incident_data.title,
            description=incident_data.description,
            severity=incident_data.severity,
            status=IncidentStatus.OPEN,
            region=incident_data.region,
            service=incident_data.service,
            root_cause_hypothesis=incident_data.root_cause_hypothesis,
            corrective_actions=incident_data.corrective_actions,
            recommended_playbook=incident_data.recommended_playbook,
            labels=incident_data.labels,
            alert_fingerprint=incident_data.alert_fingerprint,
            created_at=datetime.utcnow()
        )

        self._incidents[incident_id] = incident
        logger.info("Incident created", incident_id=incident_id, title=incident.title)

        return incident

    async def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get an incident by ID."""
        return self._incidents.get(incident_id)

    async def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        region: Optional[str] = None,
        service: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Incident]:
        """List incidents with optional filters."""
        incidents = list(self._incidents.values())

        # Apply filters
        if status:
            incidents = [i for i in incidents if i.status == status]
        if severity:
            incidents = [i for i in incidents if i.severity == severity]
        if region:
            incidents = [i for i in incidents if i.region == region]
        if service:
            incidents = [i for i in incidents if i.service == service]

        # Sort by created_at descending (newest first)
        incidents.sort(key=lambda i: i.created_at, reverse=True)

        # Apply pagination
        return incidents[offset:offset + limit]

    async def update_incident(
        self,
        incident_id: str,
        update_data: IncidentUpdate
    ) -> Optional[Incident]:
        """Update an incident."""
        incident = self._incidents.get(incident_id)
        if not incident:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(incident, field, value)

        incident.updated_at = datetime.utcnow()

        # Track status changes
        if update_data.status == IncidentStatus.ACKNOWLEDGED:
            incident.acknowledged_at = datetime.utcnow()
        elif update_data.status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
            incident.resolved_at = datetime.utcnow()

        self._incidents[incident_id] = incident
        logger.info("Incident updated", incident_id=incident_id)

        return incident

    async def get_incident_stats(self) -> Dict:
        """Get incident statistics."""
        incidents = list(self._incidents.values())

        stats = {
            "total": len(incidents),
            "by_status": {},
            "by_severity": {},
            "by_region": {}
        }

        for status in IncidentStatus:
            count = len([i for i in incidents if i.status == status])
            stats["by_status"][status.value] = count

        for severity in IncidentSeverity:
            count = len([i for i in incidents if i.severity == severity])
            stats["by_severity"][severity.value] = count

        for region in ["india", "china", "usa"]:
            count = len([i for i in incidents if i.region == region])
            stats["by_region"][region] = count

        return stats


# Singleton instance
incident_service = IncidentService()
