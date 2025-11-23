// API Types for NexusGuard NOC

export type IncidentSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type IncidentStatus = 'open' | 'acknowledged' | 'in_progress' | 'resolved' | 'closed';
export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
export type PlaybookExecutionStatus = 'pending' | 'running' | 'success' | 'failed' | 'cancelled';

export interface TransactionMetrics {
  total_count: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  error_rate: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  transactions_per_second: number;
  hash_mismatch_count: number;
  blockchain_failures: number;
}

export interface FirewallMetrics {
  total_firewalls: number;
  firewalls_up: number;
  accepts_per_second: number;
  denies_per_second: number;
  total_accepts: number;
  total_denies: number;
  deny_rate: number;
  sessions_active: number;
  sessions_max: number;
  cpu_usage: number;
  memory_usage: number;
  throughput_mbps: number;
  blocked_threats: number;
  vpn_tunnels_active: number;
}

export interface Layer3Metrics {
  total_routers: number;
  routers_up: number;
  bgp_sessions_total: number;
  bgp_sessions_established: number;
  ospf_neighbors_total: number;
  ospf_neighbors_full: number;
  routes_total: number;
  routes_bgp: number;
  routes_ospf: number;
  routes_static: number;
  packets_forwarded: number;
  packets_dropped: number;
  cpu_usage: number;
  memory_usage: number;
}

export interface Layer4Metrics {
  total_load_balancers: number;
  load_balancers_up: number;
  active_connections: number;
  connections_per_second: number;
  total_bandwidth_mbps: number;
  ssl_tps: number;
  ssl_handshakes: number;
  backend_servers_total: number;
  backend_servers_healthy: number;
  health_check_failures: number;
  session_persistence_hits: number;
  cpu_usage: number;
  memory_usage: number;
}

export interface NetworkMetrics {
  devices_total: number;
  devices_up: number;
  devices_down: number;
  avg_interface_utilization: number;
  total_errors: number;
  total_drops: number;
  firewall_accepts: number;
  firewall_denies: number;
  firewall?: FirewallMetrics;
  layer3?: Layer3Metrics;
  layer4?: Layer4Metrics;
}

export interface InfrastructureMetrics {
  avg_cpu_usage: number;
  avg_memory_usage: number;
  avg_disk_usage: number;
  total_servers: number;
  healthy_servers: number;
  db_connections_active: number;
  db_connections_max: number;
  db_avg_query_latency_ms: number;
  db_replication_lag_ms: number;
}

export interface RegionMetrics {
  region: string;
  transactions: TransactionMetrics;
  network: NetworkMetrics;
  infrastructure: InfrastructureMetrics;
  timestamp: string;
}

export interface MetricsSummary {
  global_transactions: TransactionMetrics;
  global_network: NetworkMetrics;
  global_infrastructure: InfrastructureMetrics;
  regions: RegionMetrics[];
  timestamp: string;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  region: string;
  service: string;
  root_cause_hypothesis?: string;
  corrective_actions?: string[];
  recommended_playbook?: string;
  labels?: Record<string, string>;
  created_at: string;
  updated_at?: string;
  resolved_at?: string;
  acknowledged_at?: string;
  assigned_to?: string;
  resolution_notes?: string;
}

export interface Playbook {
  id: string;
  name: string;
  description: string;
  category: string;
  incident_types: string[];
  parameters: PlaybookParameter[];
  steps: PlaybookStep[];
  requires_approval: boolean;
  is_automated: boolean;
  file_path: string;
}

export interface PlaybookParameter {
  name: string;
  description: string;
  type: string;
  required: boolean;
  default?: unknown;
}

export interface PlaybookStep {
  order: number;
  name: string;
  description: string;
  is_destructive: boolean;
}

export interface PlaybookExecution {
  id: string;
  playbook_id: string;
  incident_id?: string;
  status: PlaybookExecutionStatus;
  started_at: string;
  completed_at?: string;
  executed_by: string;
  parameters: Record<string, unknown>;
  target_hosts: string[];
  output?: string;
  error?: string;
  dry_run: boolean;
}

export interface ServiceHealth {
  name: string;
  status: HealthStatus;
  region?: string;
  latency_ms?: number;
  last_check: string;
  message?: string;
}

export interface SystemHealth {
  status: HealthStatus;
  services: ServiceHealth[];
  timestamp: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: string;
  region?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Compliance Types
export type ComplianceStatus = 'compliant' | 'non_compliant' | 'partial' | 'pending_review' | 'not_applicable';
export type ComplianceSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export interface ComplianceControl {
  id: string;
  name: string;
  description: string;
  category: string;
  status: ComplianceStatus;
  severity: ComplianceSeverity;
  evidence?: string;
  remediation?: string;
  last_assessed: string;
  next_review?: string;
  automated_check: boolean;
  playbook_id?: string;
}

export interface ComplianceFramework {
  id: string;
  name: string;
  version: string;
  description: string;
  effective_date: string;
  controls: ComplianceControl[];
  overall_status: ComplianceStatus;
  compliance_score: number;
  last_audit?: string;
  next_audit?: string;
}

export interface ComplianceAuditLog {
  id: string;
  framework_id: string;
  control_id: string;
  action: string;
  previous_status?: ComplianceStatus;
  new_status: ComplianceStatus;
  performed_by: string;
  timestamp: string;
  notes?: string;
}

export interface ComplianceSummary {
  total_frameworks: number;
  total_controls: number;
  compliant: number;
  partial: number;
  non_compliant: number;
  pending_review: number;
  overall_score: number;
  frameworks: {
    id: string;
    name: string;
    score: number;
    status: string;
    control_count: number;
  }[];
}

// Vault Types
export type VaultStatus = 'sealed' | 'unsealed' | 'standby' | 'active' | 'error' | 'unknown';
export type VaultSecretEngine = 'kv-v1' | 'kv-v2' | 'database' | 'aws' | 'ssh' | 'pki' | 'transit';
export type VaultAuthMethod = 'token' | 'userpass' | 'approle' | 'kubernetes' | 'ldap' | 'oidc';

export interface VaultHealth {
  status: VaultStatus;
  version?: string;
  cluster_name?: string;
  cluster_id?: string;
  server_time_utc?: string;
  standby: boolean;
  sealed: boolean;
  performance_standby: boolean;
}

export interface VaultSecretPath {
  id: string;
  name: string;
  path: string;
  engine: VaultSecretEngine;
  description?: string;
  last_accessed?: string;
  access_count: number;
}

export interface AnsibleVaultIntegration {
  id: string;
  playbook_id: string;
  secret_paths: string[];
  environment_variables: Record<string, string>;
  inject_as: string;
  enabled: boolean;
  last_used?: string;
}

export interface VaultPolicy {
  name: string;
  rules: {
    path: string;
    capabilities: string[];
  }[];
  created_at?: string;
  updated_at?: string;
}

export interface VaultSummary {
  status: string;
  version?: string;
  sealed: boolean;
  cluster_name?: string;
  secret_paths_count: number;
  ansible_integrations_count: number;
  enabled_integrations: number;
  policies_count: number;
  auth_method: string;
  address: string;
  engines_in_use: string[];
}
