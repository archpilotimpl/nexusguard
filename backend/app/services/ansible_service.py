"""Ansible playbook execution service."""
import os
import json
import uuid
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import (
    Playbook,
    PlaybookParameter,
    PlaybookStep,
    PlaybookExecution,
    PlaybookExecutionStatus,
    PlaybookExecutionRequest,
)

logger = get_logger(__name__)


class AnsibleService:
    """Service for managing and executing Ansible playbooks."""

    def __init__(self):
        self.playbooks_path = Path(settings.ANSIBLE_PLAYBOOKS_PATH)
        self.inventory_path = Path(settings.ANSIBLE_INVENTORY_PATH)
        self.roles_path = Path(settings.ANSIBLE_ROLES_PATH)
        self._executions: Dict[str, PlaybookExecution] = {}

    def _get_playbook_metadata(self, playbook_file: Path) -> Dict[str, Any]:
        """Extract metadata from playbook YAML header comments."""
        metadata = {
            "name": playbook_file.stem.replace("_", " ").title(),
            "description": "No description provided",
            "category": "general",
            "incident_types": [],
            "parameters": [],
            "requires_approval": False,
            "is_automated": False,
        }

        try:
            content = playbook_file.read_text()
            # Parse YAML front matter style metadata from comments
            for line in content.split("\n"):
                if line.startswith("# @"):
                    key, _, value = line[3:].partition(":")
                    key = key.strip().lower()
                    value = value.strip()

                    if key == "name":
                        metadata["name"] = value
                    elif key == "description":
                        metadata["description"] = value
                    elif key == "category":
                        metadata["category"] = value
                    elif key == "incident_types":
                        metadata["incident_types"] = [t.strip() for t in value.split(",")]
                    elif key == "requires_approval":
                        metadata["requires_approval"] = value.lower() == "true"
                    elif key == "is_automated":
                        metadata["is_automated"] = value.lower() == "true"
        except Exception as e:
            logger.warning(f"Failed to read playbook metadata: {e}")

        return metadata

    def _get_playbook_steps(self, playbook_id: str) -> List[PlaybookStep]:
        """Get execution steps for a playbook."""
        # Define steps for each playbook
        steps_map = {
            "restart_application": [
                PlaybookStep(order=1, name="Verify Service", description="Check that the application service exists and is manageable"),
                PlaybookStep(order=2, name="Pre-restart Health Check", description="Verify current health status before restart"),
                PlaybookStep(order=3, name="Stop Service", description="Gracefully stop the application service", is_destructive=True),
                PlaybookStep(order=4, name="Drain Connections", description="Wait for active connections to complete"),
                PlaybookStep(order=5, name="Clear Cache", description="Optionally clear application cache if specified"),
                PlaybookStep(order=6, name="Start Service", description="Start the application service"),
                PlaybookStep(order=7, name="Health Check", description="Wait for service to pass health checks"),
                PlaybookStep(order=8, name="Verify Running", description="Confirm service is running correctly"),
            ],
            "high_error_rate_investigation": [
                PlaybookStep(order=1, name="Collect System Info", description="Gather uptime, memory, and disk usage"),
                PlaybookStep(order=2, name="Analyze Logs", description="Extract recent errors from application logs"),
                PlaybookStep(order=3, name="Count Error Types", description="Categorize and count errors by type"),
                PlaybookStep(order=4, name="Check Database", description="Test database connectivity and connections"),
                PlaybookStep(order=5, name="Check Dependencies", description="Verify external service availability"),
                PlaybookStep(order=6, name="Generate Report", description="Compile investigation results and recommendations"),
            ],
            "disk_cleanup": [
                PlaybookStep(order=1, name="Check Initial Usage", description="Record current disk usage"),
                PlaybookStep(order=2, name="Clean Old Logs", description="Remove log files older than retention period", is_destructive=True),
                PlaybookStep(order=3, name="Clean Temp Files", description="Remove temporary files", is_destructive=True),
                PlaybookStep(order=4, name="Vacuum Journal", description="Clean systemd journal logs"),
                PlaybookStep(order=5, name="Clean Package Cache", description="Remove package manager cache"),
                PlaybookStep(order=6, name="Verify Results", description="Check final disk usage and report freed space"),
            ],
            "network_device_recovery": [
                PlaybookStep(order=1, name="Ping Test", description="Test basic network connectivity to device"),
                PlaybookStep(order=2, name="SSH Check", description="Verify management port accessibility"),
                PlaybookStep(order=3, name="OOB Access", description="Try out-of-band management if primary fails"),
                PlaybookStep(order=4, name="Collect Diagnostics", description="Gather device information if accessible"),
                PlaybookStep(order=5, name="Generate Report", description="Create recovery report with recommendations"),
            ],
            "collect_diagnostics": [
                PlaybookStep(order=1, name="Create Directory", description="Create temporary directory for diagnostics"),
                PlaybookStep(order=2, name="System Info", description="Collect uname, uptime, memory, disk, processes"),
                PlaybookStep(order=3, name="Network Info", description="Gather interfaces, routes, ports, connections"),
                PlaybookStep(order=4, name="System Logs", description="Collect recent journal and dmesg logs"),
                PlaybookStep(order=5, name="Create Archive", description="Package all diagnostics into tar.gz"),
            ],
            "service_health_check": [
                PlaybookStep(order=1, name="Check Services", description="Verify systemd service status"),
                PlaybookStep(order=2, name="Check Endpoints", description="Test health check URLs"),
                PlaybookStep(order=3, name="Count Processes", description="Check running process counts"),
                PlaybookStep(order=4, name="Check FDs", description="Check file descriptor usage"),
                PlaybookStep(order=5, name="Generate Report", description="Compile health status report"),
            ],
            "database_failover": [
                PlaybookStep(order=1, name="Verify Primary Down", description="Confirm primary database is unreachable"),
                PlaybookStep(order=2, name="Verify Replica Up", description="Confirm replica is accessible"),
                PlaybookStep(order=3, name="Promote Replica", description="Execute pg_promote() on replica", is_destructive=True),
                PlaybookStep(order=4, name="Wait for Promotion", description="Wait for promotion to complete"),
                PlaybookStep(order=5, name="Verify Writable", description="Confirm new primary accepts writes"),
                PlaybookStep(order=6, name="Update Config", description="Update application database configuration"),
                PlaybookStep(order=7, name="Generate Report", description="Create failover report with next steps"),
            ],
            "memory_pressure_relief": [
                PlaybookStep(order=1, name="Check Memory", description="Record current memory usage"),
                PlaybookStep(order=2, name="Clear Caches", description="Drop page cache, dentries, inodes", is_destructive=True),
                PlaybookStep(order=3, name="Clean Journal", description="Vacuum systemd journal logs"),
                PlaybookStep(order=4, name="Kill Zombies", description="Terminate zombie processes"),
                PlaybookStep(order=5, name="Restart Services", description="Restart memory-heavy services if specified", is_destructive=True),
                PlaybookStep(order=6, name="Clean Temp", description="Remove old temporary files"),
                PlaybookStep(order=7, name="Verify Results", description="Check memory freed"),
            ],
            "ssl_certificate_check": [
                PlaybookStep(order=1, name="Check Expiration", description="Query certificate expiration dates"),
                PlaybookStep(order=2, name="Get Details", description="Extract certificate subject and dates"),
                PlaybookStep(order=3, name="Generate Report", description="Create certificate status report"),
                PlaybookStep(order=4, name="Alert Expiring", description="Flag certificates expiring soon"),
            ],
            "log_rotation_emergency": [
                PlaybookStep(order=1, name="Check Disk", description="Record initial disk usage"),
                PlaybookStep(order=2, name="Force Rotate", description="Execute logrotate forcefully"),
                PlaybookStep(order=3, name="Compress Logs", description="Compress uncompressed log files"),
                PlaybookStep(order=4, name="Remove Old", description="Delete old compressed logs", is_destructive=True),
                PlaybookStep(order=5, name="Truncate Large", description="Truncate oversized active logs", is_destructive=True),
                PlaybookStep(order=6, name="Clean Journal", description="Vacuum journal to 100MB"),
                PlaybookStep(order=7, name="Verify Results", description="Report space freed"),
            ],
            "connection_pool_reset": [
                PlaybookStep(order=1, name="Check Connections", description="Count current DB/Redis connections"),
                PlaybookStep(order=2, name="Stop Application", description="Gracefully stop application", is_destructive=True),
                PlaybookStep(order=3, name="Wait for Close", description="Wait for connections to terminate"),
                PlaybookStep(order=4, name="Start Application", description="Start application service"),
                PlaybookStep(order=5, name="Health Check", description="Wait for application to be healthy"),
                PlaybookStep(order=6, name="Verify Results", description="Check new connection count"),
            ],
            "network_connectivity_test": [
                PlaybookStep(order=1, name="Test Internal", description="Check connectivity to internal services"),
                PlaybookStep(order=2, name="Test External", description="Check connectivity to external endpoints"),
                PlaybookStep(order=3, name="Test DNS", description="Verify DNS resolution"),
                PlaybookStep(order=4, name="Test Gateway", description="Ping default gateway"),
                PlaybookStep(order=5, name="Generate Report", description="Compile connectivity report"),
            ],
            "kubernetes_pod_restart": [
                PlaybookStep(order=1, name="Set Context", description="Switch to target Kubernetes context"),
                PlaybookStep(order=2, name="Check Status", description="Get current deployment status"),
                PlaybookStep(order=3, name="List Pods", description="Show pods before restart"),
                PlaybookStep(order=4, name="Rolling Restart", description="Execute rollout restart", is_destructive=True),
                PlaybookStep(order=5, name="Wait Rollout", description="Wait for rollout to complete"),
                PlaybookStep(order=6, name="Verify Pods", description="Show pods after restart"),
                PlaybookStep(order=7, name="Check Health", description="Verify deployment is healthy"),
            ],
            "redis_cache_flush": [
                PlaybookStep(order=1, name="Get Stats Before", description="Record memory and key count"),
                PlaybookStep(order=2, name="Flush Cache", description="Execute FLUSHDB or FLUSHALL", is_destructive=True),
                PlaybookStep(order=3, name="Get Stats After", description="Record new memory and key count"),
                PlaybookStep(order=4, name="Generate Report", description="Report cache flush results"),
            ],
            "load_balancer_drain": [
                PlaybookStep(order=1, name="Set Drain Mode", description="Mark server for connection draining"),
                PlaybookStep(order=2, name="Wait Drain", description="Wait for active connections to complete"),
                PlaybookStep(order=3, name="Set Maintenance", description="Put server in maintenance mode", is_destructive=True),
                PlaybookStep(order=4, name="Confirm Status", description="Verify server is removed from rotation"),
            ],
            "blockchain_node_recovery": [
                PlaybookStep(order=1, name="Check Sync", description="Query current sync status"),
                PlaybookStep(order=2, name="Stop Service", description="Stop blockchain service", is_destructive=True),
                PlaybookStep(order=3, name="Backup Data", description="Archive current chain data"),
                PlaybookStep(order=4, name="Clear Locks", description="Remove corrupted lock files"),
                PlaybookStep(order=5, name="Start Service", description="Start blockchain service"),
                PlaybookStep(order=6, name="Wait Sync", description="Wait for node to start syncing"),
                PlaybookStep(order=7, name="Check Peers", description="Verify peer connections"),
            ],
            "api_rate_limit_adjust": [
                PlaybookStep(order=1, name="Backup Config", description="Backup current rate limit configuration"),
                PlaybookStep(order=2, name="Read Current", description="Display current rate limit"),
                PlaybookStep(order=3, name="Update Limit", description="Apply new rate limit value", is_destructive=True),
                PlaybookStep(order=4, name="Reload App", description="Reload application configuration"),
                PlaybookStep(order=5, name="Schedule Revert", description="Schedule automatic revert if duration set"),
            ],
            "firewall_emergency_block": [
                PlaybookStep(order=1, name="Block IPs", description="Add iptables DROP rules for malicious IPs", is_destructive=True),
                PlaybookStep(order=2, name="Block Ports", description="Add iptables rules to block ports", is_destructive=True),
                PlaybookStep(order=3, name="Enable Logging", description="Log blocked connection attempts"),
                PlaybookStep(order=4, name="Save Rules", description="Persist iptables rules"),
                PlaybookStep(order=5, name="Schedule Unblock", description="Schedule automatic unblock if duration set"),
            ],
            "firewall_session_cleanup": [
                PlaybookStep(order=1, name="Check Sessions", description="Query current firewall session count"),
                PlaybookStep(order=2, name="Calculate Utilization", description="Determine session utilization percentage"),
                PlaybookStep(order=3, name="Backup Config", description="Backup firewall configuration"),
                PlaybookStep(order=4, name="Clear Idle Sessions", description="Remove sessions exceeding idle timeout", is_destructive=True),
                PlaybookStep(order=5, name="Verify Cleanup", description="Check session count after cleanup"),
                PlaybookStep(order=6, name="Send Notification", description="Alert NOC of cleanup results"),
            ],
            "bgp_session_recovery": [
                PlaybookStep(order=1, name="Check BGP Status", description="Query BGP session states"),
                PlaybookStep(order=2, name="Identify Down Peers", description="List BGP neighbors in Idle/Active/Connect state"),
                PlaybookStep(order=3, name="Check Routes", description="Count BGP routes before recovery"),
                PlaybookStep(order=4, name="Soft Reset", description="Execute soft BGP reset (clear ip bgp soft)", is_destructive=True),
                PlaybookStep(order=5, name="Wait for Convergence", description="Allow time for BGP to re-establish"),
                PlaybookStep(order=6, name="Verify Recovery", description="Confirm BGP sessions are established"),
                PlaybookStep(order=7, name="Hard Reset if Needed", description="Execute hard reset if soft reset failed", is_destructive=True),
                PlaybookStep(order=8, name="Collect Diagnostics", description="Gather BGP neighbor details for failed sessions"),
            ],
            "ospf_neighbor_recovery": [
                PlaybookStep(order=1, name="Check OSPF Neighbors", description="Query OSPF neighbor adjacency states"),
                PlaybookStep(order=2, name="Identify Non-Full", description="List neighbors not in FULL state"),
                PlaybookStep(order=3, name="Check Interfaces", description="Verify OSPF interface status"),
                PlaybookStep(order=4, name="Clear OSPF Process", description="Reset OSPF process to trigger re-convergence", is_destructive=True),
                PlaybookStep(order=5, name="Wait for Adjacency", description="Allow time for OSPF to form adjacencies"),
                PlaybookStep(order=6, name="Verify Recovery", description="Confirm OSPF neighbors in FULL state"),
                PlaybookStep(order=7, name="Check Route Count", description="Validate OSPF routes in routing table"),
                PlaybookStep(order=8, name="Collect Database", description="Gather OSPF database for troubleshooting"),
            ],
            "load_balancer_backend_health": [
                PlaybookStep(order=1, name="Check Backend Status", description="Query backend server health status"),
                PlaybookStep(order=2, name="Calculate Health %", description="Determine percentage of healthy backends"),
                PlaybookStep(order=3, name="Alert if Degraded", description="Send alert if health below threshold"),
                PlaybookStep(order=4, name="Re-enable Backends", description="Attempt to enable unhealthy backends", is_destructive=True),
                PlaybookStep(order=5, name="Re-check Health", description="Verify backend health after recovery"),
                PlaybookStep(order=6, name="Check SSL Certs", description="Identify expiring SSL certificates"),
                PlaybookStep(order=7, name="Check Metrics", description="Collect active connections and SSL TPS"),
                PlaybookStep(order=8, name="Drain if Failed", description="Disable backends if recovery unsuccessful", is_destructive=True),
            ],
        }

        return steps_map.get(playbook_id, [
            PlaybookStep(order=1, name="Execute Playbook", description="Run the Ansible playbook tasks")
        ])

    async def list_playbooks(self, category: Optional[str] = None) -> List[Playbook]:
        """List all available playbooks."""
        playbooks = []

        if not self.playbooks_path.exists():
            logger.warning(f"Playbooks directory not found: {self.playbooks_path}")
            return playbooks

        # Search for playbooks in root directory and subdirectories
        for playbook_file in self.playbooks_path.glob("**/*.yml"):
            # Skip inventory files
            if "inventory" in str(playbook_file):
                continue

            metadata = self._get_playbook_metadata(playbook_file)

            # Infer category from subdirectory if not explicitly set
            if playbook_file.parent != self.playbooks_path:
                inferred_category = playbook_file.parent.name
                if metadata["category"] == "general":
                    metadata["category"] = inferred_category

            if category and metadata["category"] != category:
                continue

            playbook = Playbook(
                id=playbook_file.stem,
                name=metadata["name"],
                description=metadata["description"],
                category=metadata["category"],
                incident_types=metadata["incident_types"],
                parameters=metadata.get("parameters", []),
                steps=self._get_playbook_steps(playbook_file.stem),
                requires_approval=metadata["requires_approval"],
                is_automated=metadata["is_automated"],
                file_path=str(playbook_file)
            )
            playbooks.append(playbook)

        return playbooks

    async def get_playbook(self, playbook_id: str) -> Optional[Playbook]:
        """Get a specific playbook by ID."""
        playbooks = await self.list_playbooks()
        for pb in playbooks:
            if pb.id == playbook_id:
                return pb
        return None

    async def execute_playbook(
        self,
        request: PlaybookExecutionRequest,
        executed_by: str
    ) -> PlaybookExecution:
        """Execute an Ansible playbook."""
        execution_id = str(uuid.uuid4())

        # Get playbook details
        playbook = await self.get_playbook(request.playbook_id)
        if not playbook:
            raise ValueError(f"Playbook not found: {request.playbook_id}")

        # Create execution record
        execution = PlaybookExecution(
            id=execution_id,
            playbook_id=request.playbook_id,
            incident_id=request.incident_id,
            status=PlaybookExecutionStatus.PENDING,
            started_at=datetime.utcnow(),
            executed_by=executed_by,
            parameters=request.parameters or {},
            target_hosts=request.target_hosts or ["all"],
            dry_run=request.dry_run
        )

        self._executions[execution_id] = execution

        # Run playbook in background
        asyncio.create_task(
            self._run_playbook(execution, playbook)
        )

        return execution

    async def _run_playbook(self, execution: PlaybookExecution, playbook: Playbook) -> None:
        """Run the actual playbook using ansible-runner."""
        try:
            execution.status = PlaybookExecutionStatus.RUNNING
            self._executions[execution.id] = execution

            # Build ansible-playbook command
            cmd = [
                "ansible-playbook",
                playbook.file_path,
                "-i", str(self.inventory_path / "hosts.yml"),
            ]

            # Add limit for target hosts
            if execution.target_hosts and execution.target_hosts != ["all"]:
                cmd.extend(["-l", ",".join(execution.target_hosts)])

            # Add extra variables
            if execution.parameters:
                extra_vars = json.dumps(execution.parameters)
                cmd.extend(["-e", extra_vars])

            # Dry run mode
            if execution.dry_run:
                cmd.append("--check")

            logger.info(
                "Executing playbook",
                execution_id=execution.id,
                playbook=playbook.name,
                command=" ".join(cmd)
            )

            # Execute the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            execution.completed_at = datetime.utcnow()
            execution.output = stdout.decode() if stdout else ""

            if process.returncode == 0:
                execution.status = PlaybookExecutionStatus.SUCCESS
                logger.info("Playbook completed successfully", execution_id=execution.id)
            else:
                execution.status = PlaybookExecutionStatus.FAILED
                execution.error = stderr.decode() if stderr else "Unknown error"
                logger.error(
                    "Playbook failed",
                    execution_id=execution.id,
                    error=execution.error
                )

        except Exception as e:
            execution.status = PlaybookExecutionStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.error = str(e)
            logger.error("Playbook execution error", execution_id=execution.id, error=str(e))

        self._executions[execution.id] = execution

    async def get_execution(self, execution_id: str) -> Optional[PlaybookExecution]:
        """Get execution status by ID."""
        return self._executions.get(execution_id)

    async def list_executions(
        self,
        playbook_id: Optional[str] = None,
        incident_id: Optional[str] = None,
        limit: int = 50
    ) -> List[PlaybookExecution]:
        """List playbook executions with optional filters."""
        executions = list(self._executions.values())

        if playbook_id:
            executions = [e for e in executions if e.playbook_id == playbook_id]

        if incident_id:
            executions = [e for e in executions if e.incident_id == incident_id]

        # Sort by started_at descending
        executions.sort(key=lambda e: e.started_at, reverse=True)

        return executions[:limit]

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running playbook execution."""
        execution = self._executions.get(execution_id)
        if not execution:
            return False

        if execution.status == PlaybookExecutionStatus.RUNNING:
            execution.status = PlaybookExecutionStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            self._executions[execution_id] = execution
            return True

        return False


# Singleton instance
ansible_service = AnsibleService()
