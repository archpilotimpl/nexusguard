# NexusGuard NOC Ansible Playbooks

Automated remediation playbooks for incident response and infrastructure management across global regions (India, USA, China).

## Directory Structure

```
playbooks/
├── network/              # Network infrastructure playbooks
├── infrastructure/       # Server and database playbooks
├── application/          # Application service playbooks
└── security/            # Security and compliance playbooks
```

## Network Playbooks

### Firewall Management
- **`firewall_session_cleanup.yml`** - Clean up firewall sessions when utilization exceeds threshold
  - Monitors session utilization percentage
  - Supports safe (idle timeout) and aggressive (specific IP) cleanup modes
  - Backs up configuration before cleanup
  - **Use case**: Firewall session utilization > 75%

- **`firewall_emergency_block.yml`** - Emergency IP/network blocking for security threats
  - Rapid threat response
  - Blocks malicious IPs or networks
  - **Use case**: Active security threats detected

### Layer 3 (Routing) Management
- **`bgp_session_recovery.yml`** - Recover down BGP sessions and restore routing
  - Identifies idle/active/connecting BGP peers
  - Attempts soft reset first, then hard reset
  - Validates route count before/after
  - **Use case**: BGP sessions not established

- **`ospf_neighbor_recovery.yml`** - Repair OSPF adjacencies and neighbor relationships
  - Checks OSPF neighbor states (not FULL)
  - Clears OSPF process to trigger re-convergence
  - Collects database dumps for troubleshooting
  - **Use case**: OSPF neighbors stuck in INIT/2WAY/EXSTART

- **`network_device_recovery.yml`** - Generic network device recovery
  - Device reboot and configuration reload
  - **Use case**: Network device unresponsive

- **`network_connectivity_test.yml`** - Comprehensive network connectivity testing
  - End-to-end connectivity validation
  - **Use case**: Network reachability issues

### Layer 4 (Load Balancing) Management
- **`load_balancer_backend_health.yml`** - Monitor and repair backend server health
  - Checks backend server monitor status
  - Attempts to re-enable failed backends
  - Monitors SSL certificate expiration
  - Tracks SSL TPS and active connections
  - **Use case**: Backend server health < 95%

- **`load_balancer_drain.yml`** - Gracefully drain load balancer connections
  - Connection draining for maintenance
  - **Use case**: Planned maintenance or upgrades

## Infrastructure Playbooks

- **`database_failover.yml`** - Failover to standby database
  - Promotes replica to master
  - **Use case**: Primary database failure

- **`disk_cleanup.yml`** - Emergency disk space cleanup
  - Removes old logs and temporary files
  - **Use case**: Disk usage > 80%

- **`memory_pressure_relief.yml`** - Release memory pressure
  - Clears caches and buffers
  - **Use case**: Memory usage > 85%

- **`connection_pool_reset.yml`** - Reset database connection pools
  - Clears stuck connections
  - **Use case**: Connection pool exhaustion

- **`log_rotation_emergency.yml`** - Emergency log file rotation
  - Compresses and archives logs
  - **Use case**: Log files consuming disk space

## Application Playbooks

- **`restart_application.yml`** - Graceful application restart
  - Rolling restart across instances
  - **Use case**: Application hangs or memory leaks

- **`high_error_rate_investigation.yml`** - Investigate transaction error spikes
  - Collects error logs and traces
  - **Use case**: Error rate > 1%

- **`collect_diagnostics.yml`** - Comprehensive diagnostic collection
  - Gathers logs, metrics, and system state
  - **Use case**: Troubleshooting incidents

- **`service_health_check.yml`** - Multi-service health validation
  - Checks all service endpoints
  - **Use case**: Health check verification

- **`kubernetes_pod_restart.yml`** - Restart Kubernetes pods
  - Rolling pod restart with health checks
  - **Use case**: Pod issues or configuration updates

- **`redis_cache_flush.yml`** - Flush Redis cache
  - Clears stale cache data
  - **Use case**: Cache corruption or invalidation

- **`blockchain_node_recovery.yml`** - Recover blockchain node
  - Resync blockchain data
  - **Use case**: Blockchain hash mismatches

- **`api_rate_limit_adjust.yml`** - Dynamically adjust API rate limits
  - Responds to traffic spikes
  - **Use case**: Rate limiting during high load

## Security Playbooks

- **`ssl_certificate_check.yml`** - SSL/TLS certificate expiration monitoring
  - Validates certificate expiration dates
  - Alerts on certificates expiring within 30 days
  - **Use case**: Preventive certificate renewal

## Usage

### Prerequisites
- Ansible 2.9+
- Valid inventory file (`../inventory/hosts.yml`)
- Vault credentials configured for secure operations
- Network access to target devices

### Running a Playbook

```bash
# Basic execution
ansible-playbook -i ../inventory/hosts.yml network/firewall_session_cleanup.yml

# With extra variables
ansible-playbook -i ../inventory/hosts.yml network/bgp_session_recovery.yml \
  -e "auto_recovery=true region=india"

# Dry run (check mode)
ansible-playbook -i ../inventory/hosts.yml network/load_balancer_backend_health.yml --check

# Limit to specific hosts
ansible-playbook -i ../inventory/hosts.yml infrastructure/disk_cleanup.yml \
  --limit "india-db-01"
```

### Common Variables

All playbooks support these common variables:

- `region`: Target region (india, usa, china)
- `webhook_url`: NexusGuard NOC API endpoint for incident creation
- `dry_run`: Execute in check mode without making changes
- `collect_diagnostics`: Gather diagnostic information

### Vault Integration

Playbooks automatically retrieve credentials from HashiCorp Vault when executed via the NexusGuard NOC platform. Manual execution requires vault configuration:

```bash
export VAULT_ADDR=http://vault:8200
export VAULT_TOKEN=<your-token>
```

## Metrics Integration

All playbooks integrate with the NexusGuard NOC metrics system:

- **Firewall Playbooks**: Update `noc_firewall_*` metrics
- **Layer 3 Playbooks**: Update `noc_router_*` metrics
- **Layer 4 Playbooks**: Update `noc_loadbalancer_*` metrics
- **Application Playbooks**: Update `noc_transaction_*` metrics

## Incident Workflow

1. **Detection**: Prometheus alerts trigger incident creation
2. **Analysis**: CrewAI agent analyzes metrics and suggests playbook
3. **Approval**: NOC engineer reviews and approves execution
4. **Execution**: Playbook runs with Vault-injected credentials
5. **Verification**: Post-execution health checks validate resolution
6. **Closure**: Incident updated with execution results

## Best Practices

- Always run with `--check` first for destructive operations
- Use `backup_config` for network device changes
- Monitor playbook execution via NexusGuard NOC dashboard
- Review playbook logs in incident timeline
- Test playbooks in non-production environments first

## Troubleshooting

### Playbook Execution Fails

1. Verify inventory hosts are reachable
2. Check Vault credentials are valid
3. Review playbook logs for specific errors
4. Validate target device CLI access

### Network Device Playbooks Not Working

- Ensure device-specific CLI commands match vendor (Cisco, Juniper, Palo Alto, etc.)
- Verify privilege level for commands (enable mode, config mode)
- Check device API access if using REST instead of CLI

## Contributing

When adding new playbooks:

1. Place in appropriate category directory
2. Include descriptive header with use case
3. Support common variables (region, webhook_url, dry_run)
4. Add entry to this README
5. Test in all three regions
6. Document required Vault secrets

## Related Documentation

- [NexusGuard NOC Architecture](../../README.md)
- [Vault Integration](../../docs/vault-integration.md)
- [Incident Response Guide](../../docs/incident-response.md)
- [Prometheus Metrics](../../docs/metrics.md)
