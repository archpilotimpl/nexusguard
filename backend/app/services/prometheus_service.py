"""Prometheus metrics service."""
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import (
    MetricsSummary,
    RegionMetrics,
    TransactionMetrics,
    NetworkMetrics,
    FirewallMetrics,
    Layer3Metrics,
    Layer4Metrics,
    InfrastructureMetrics,
)

logger = get_logger(__name__)


class PrometheusService:
    """Service for querying Prometheus metrics."""

    def __init__(self):
        self.base_url = settings.PROMETHEUS_URL
        self.timeout = 30.0

    async def query(self, promql: str, time: Optional[datetime] = None) -> Dict[str, Any]:
        """Execute an instant query against Prometheus."""
        params = {"query": promql}
        if time:
            params["time"] = time.isoformat()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/query",
                    params=params
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error("Prometheus query failed", query=promql, error=str(e))
                raise

    async def query_range(
        self,
        promql: str,
        start: datetime,
        end: datetime,
        step: str = "1m"
    ) -> Dict[str, Any]:
        """Execute a range query against Prometheus."""
        params = {
            "query": promql,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "step": step
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/query_range",
                    params=params
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error("Prometheus range query failed", query=promql, error=str(e))
                raise

    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current firing alerts from Prometheus."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/api/v1/alerts")
                response.raise_for_status()
                data = response.json()
                return data.get("data", {}).get("alerts", [])
            except httpx.HTTPError as e:
                logger.error("Failed to fetch alerts", error=str(e))
                raise

    def _extract_value(self, result: Dict, default: float = 0.0) -> float:
        """Extract scalar value from Prometheus query result."""
        try:
            data = result.get("data", {})
            results = data.get("result", [])
            if results:
                value = results[0].get("value", [None, default])
                return float(value[1]) if len(value) > 1 else default
        except (IndexError, ValueError, TypeError):
            pass
        return default

    async def get_transaction_metrics(self, region: Optional[str] = None) -> TransactionMetrics:
        """Get transaction metrics for a region or globally."""
        region_filter = f'region="{region}"' if region else ""

        # Define queries
        queries = {
            "total": f'sum(noc_transactions_total{{{region_filter}}})',
            "success": f'sum(noc_transactions_total{{status="success",{region_filter}}})',
            "failure": f'sum(noc_transactions_total{{status="failure",{region_filter}}})',
            "avg_latency": f'avg(noc_transaction_latency_seconds{{{region_filter}}}) * 1000',
            "p50": f'histogram_quantile(0.50, sum(rate(noc_transaction_latency_bucket{{{region_filter}}}[5m])) by (le)) * 1000',
            "p95": f'histogram_quantile(0.95, sum(rate(noc_transaction_latency_bucket{{{region_filter}}}[5m])) by (le)) * 1000',
            "p99": f'histogram_quantile(0.99, sum(rate(noc_transaction_latency_bucket{{{region_filter}}}[5m])) by (le)) * 1000',
            "tps": f'sum(rate(noc_transactions_total{{{region_filter}}}[5m]))',
            "hash_mismatch": f'sum(noc_hash_mismatch_total{{{region_filter}}})',
            "blockchain_fail": f'sum(noc_blockchain_failures_total{{{region_filter}}})',
        }

        results = {}
        for key, query in queries.items():
            try:
                result = await self.query(query)
                results[key] = self._extract_value(result)
            except Exception as e:
                logger.warning(f"Query failed for {key}", error=str(e))
                results[key] = 0.0

        total = results["total"] or 1
        success = results["success"]
        failure = results["failure"]

        return TransactionMetrics(
            total_count=int(total),
            success_count=int(success),
            failure_count=int(failure),
            success_rate=(success / total * 100) if total > 0 else 0,
            error_rate=(failure / total * 100) if total > 0 else 0,
            avg_latency_ms=results["avg_latency"],
            p50_latency_ms=results["p50"],
            p95_latency_ms=results["p95"],
            p99_latency_ms=results["p99"],
            transactions_per_second=results["tps"],
            hash_mismatch_count=int(results["hash_mismatch"]),
            blockchain_failures=int(results["blockchain_fail"])
        )

    async def get_firewall_metrics(self, region: Optional[str] = None) -> FirewallMetrics:
        """Get firewall-specific metrics."""
        region_filter = f'region="{region}"' if region else ""

        queries = {
            "total_fw": f'count(noc_firewall_up{{device_type="firewall",{region_filter}}})',
            "fw_up": f'sum(noc_firewall_up{{device_type="firewall",{region_filter}}})',
            "accept_rate": f'rate(noc_firewall_accepts_total{{{region_filter}}}[5m])',
            "deny_rate": f'rate(noc_firewall_denies_total{{{region_filter}}}[5m])',
            "total_accepts": f'sum(noc_firewall_accepts_total{{{region_filter}}})',
            "total_denies": f'sum(noc_firewall_denies_total{{{region_filter}}})',
            "sessions": f'sum(noc_firewall_sessions_active{{{region_filter}}})',
            "sessions_max": f'sum(noc_firewall_sessions_max{{{region_filter}}})',
            "fw_cpu": f'avg(noc_firewall_cpu_usage{{{region_filter}}})',
            "fw_mem": f'avg(noc_firewall_memory_usage{{{region_filter}}})',
            "throughput": f'sum(rate(noc_firewall_throughput_bytes{{{region_filter}}}[5m])) / 1000000 * 8',
            "threats": f'sum(noc_firewall_threats_blocked_total{{{region_filter}}})',
            "vpn": f'sum(noc_firewall_vpn_tunnels_active{{{region_filter}}})',
        }

        results = {}
        for key, query in queries.items():
            try:
                result = await self.query(query)
                results[key] = self._extract_value(result)
            except Exception:
                results[key] = 0.0

        total_accepts = int(results["total_accepts"])
        total_denies = int(results["total_denies"])
        total_conn = total_accepts + total_denies

        return FirewallMetrics(
            total_firewalls=int(results["total_fw"]),
            firewalls_up=int(results["fw_up"]),
            accepts_per_second=results["accept_rate"],
            denies_per_second=results["deny_rate"],
            total_accepts=total_accepts,
            total_denies=total_denies,
            deny_rate=(total_denies / total_conn * 100) if total_conn > 0 else 0,
            sessions_active=int(results["sessions"]),
            sessions_max=int(results["sessions_max"]),
            cpu_usage=results["fw_cpu"],
            memory_usage=results["fw_mem"],
            throughput_mbps=results["throughput"],
            blocked_threats=int(results["threats"]),
            vpn_tunnels_active=int(results["vpn"])
        )

    async def get_layer3_metrics(self, region: Optional[str] = None) -> Layer3Metrics:
        """Get Layer 3 router metrics."""
        region_filter = f'region="{region}"' if region else ""

        queries = {
            "total_routers": f'count(noc_router_up{{device_type="router",{region_filter}}})',
            "routers_up": f'sum(noc_router_up{{device_type="router",{region_filter}}})',
            "bgp_total": f'sum(noc_router_bgp_sessions_total{{{region_filter}}})',
            "bgp_est": f'sum(noc_router_bgp_sessions_established{{{region_filter}}})',
            "ospf_total": f'sum(noc_router_ospf_neighbors_total{{{region_filter}}})',
            "ospf_full": f'sum(noc_router_ospf_neighbors_full{{{region_filter}}})',
            "routes_total": f'sum(noc_router_routes_total{{{region_filter}}})',
            "routes_bgp": f'sum(noc_router_routes_bgp{{{region_filter}}})',
            "routes_ospf": f'sum(noc_router_routes_ospf{{{region_filter}}})',
            "routes_static": f'sum(noc_router_routes_static{{{region_filter}}})',
            "pkts_fwd": f'sum(noc_router_packets_forwarded_total{{{region_filter}}})',
            "pkts_drop": f'sum(noc_router_packets_dropped_total{{{region_filter}}})',
            "router_cpu": f'avg(noc_router_cpu_usage{{{region_filter}}})',
            "router_mem": f'avg(noc_router_memory_usage{{{region_filter}}})',
        }

        results = {}
        for key, query in queries.items():
            try:
                result = await self.query(query)
                results[key] = self._extract_value(result)
            except Exception:
                results[key] = 0.0

        return Layer3Metrics(
            total_routers=int(results["total_routers"]),
            routers_up=int(results["routers_up"]),
            bgp_sessions_total=int(results["bgp_total"]),
            bgp_sessions_established=int(results["bgp_est"]),
            ospf_neighbors_total=int(results["ospf_total"]),
            ospf_neighbors_full=int(results["ospf_full"]),
            routes_total=int(results["routes_total"]),
            routes_bgp=int(results["routes_bgp"]),
            routes_ospf=int(results["routes_ospf"]),
            routes_static=int(results["routes_static"]),
            packets_forwarded=int(results["pkts_fwd"]),
            packets_dropped=int(results["pkts_drop"]),
            cpu_usage=results["router_cpu"],
            memory_usage=results["router_mem"]
        )

    async def get_layer4_metrics(self, region: Optional[str] = None) -> Layer4Metrics:
        """Get Layer 4 load balancer metrics."""
        region_filter = f'region="{region}"' if region else ""

        queries = {
            "total_lb": f'count(noc_loadbalancer_up{{device_type="loadbalancer",{region_filter}}})',
            "lb_up": f'sum(noc_loadbalancer_up{{device_type="loadbalancer",{region_filter}}})',
            "active_conn": f'sum(noc_loadbalancer_connections_active{{{region_filter}}})',
            "conn_rate": f'sum(rate(noc_loadbalancer_connections_total{{{region_filter}}}[5m]))',
            "bandwidth": f'sum(rate(noc_loadbalancer_bandwidth_bytes{{{region_filter}}}[5m])) / 1000000 * 8',
            "ssl_tps": f'sum(rate(noc_loadbalancer_ssl_transactions_total{{{region_filter}}}[5m]))',
            "ssl_handshakes": f'sum(noc_loadbalancer_ssl_handshakes_total{{{region_filter}}})',
            "backend_total": f'sum(noc_loadbalancer_backend_servers_total{{{region_filter}}})',
            "backend_healthy": f'sum(noc_loadbalancer_backend_servers_healthy{{{region_filter}}})',
            "health_fails": f'sum(noc_loadbalancer_healthcheck_failures_total{{{region_filter}}})',
            "persist_hits": f'sum(noc_loadbalancer_session_persistence_hits_total{{{region_filter}}})',
            "lb_cpu": f'avg(noc_loadbalancer_cpu_usage{{{region_filter}}})',
            "lb_mem": f'avg(noc_loadbalancer_memory_usage{{{region_filter}}})',
        }

        results = {}
        for key, query in queries.items():
            try:
                result = await self.query(query)
                results[key] = self._extract_value(result)
            except Exception:
                results[key] = 0.0

        return Layer4Metrics(
            total_load_balancers=int(results["total_lb"]),
            load_balancers_up=int(results["lb_up"]),
            active_connections=int(results["active_conn"]),
            connections_per_second=results["conn_rate"],
            total_bandwidth_mbps=results["bandwidth"],
            ssl_tps=results["ssl_tps"],
            ssl_handshakes=int(results["ssl_handshakes"]),
            backend_servers_total=int(results["backend_total"]),
            backend_servers_healthy=int(results["backend_healthy"]),
            health_check_failures=int(results["health_fails"]),
            session_persistence_hits=int(results["persist_hits"]),
            cpu_usage=results["lb_cpu"],
            memory_usage=results["lb_mem"]
        )

    async def get_network_metrics(self, region: Optional[str] = None) -> NetworkMetrics:
        """Get comprehensive network device metrics."""
        region_filter = f'region="{region}"' if region else ""

        queries = {
            "total": f'count(noc_device_up{{{region_filter}}})',
            "up": f'sum(noc_device_up{{{region_filter}}})',
            "utilization": f'avg(noc_interface_utilization{{{region_filter}}})',
            "errors": f'sum(noc_interface_errors_total{{{region_filter}}})',
            "drops": f'sum(noc_interface_drops_total{{{region_filter}}})',
            "fw_accept": f'sum(noc_firewall_accepts_total{{{region_filter}}})',
            "fw_deny": f'sum(noc_firewall_denies_total{{{region_filter}}})',
        }

        results = {}
        for key, query in queries.items():
            try:
                result = await self.query(query)
                results[key] = self._extract_value(result)
            except Exception:
                results[key] = 0.0

        total = int(results["total"])
        up = int(results["up"])

        # Get detailed layer-specific metrics
        try:
            firewall_metrics = await self.get_firewall_metrics(region)
        except Exception as e:
            logger.warning("Failed to get firewall metrics", error=str(e))
            firewall_metrics = None

        try:
            layer3_metrics = await self.get_layer3_metrics(region)
        except Exception as e:
            logger.warning("Failed to get layer3 metrics", error=str(e))
            layer3_metrics = None

        try:
            layer4_metrics = await self.get_layer4_metrics(region)
        except Exception as e:
            logger.warning("Failed to get layer4 metrics", error=str(e))
            layer4_metrics = None

        return NetworkMetrics(
            devices_total=total,
            devices_up=up,
            devices_down=total - up,
            avg_interface_utilization=results["utilization"],
            total_errors=int(results["errors"]),
            total_drops=int(results["drops"]),
            firewall_accepts=int(results["fw_accept"]),
            firewall_denies=int(results["fw_deny"]),
            firewall=firewall_metrics,
            layer3=layer3_metrics,
            layer4=layer4_metrics
        )

    async def get_infrastructure_metrics(self, region: Optional[str] = None) -> InfrastructureMetrics:
        """Get infrastructure metrics for servers and databases."""
        region_filter = f'region="{region}"' if region else ""

        queries = {
            "cpu": f'avg(noc_server_cpu_usage{{{region_filter}}})',
            "memory": f'avg(noc_server_memory_usage{{{region_filter}}})',
            "disk": f'avg(noc_server_disk_usage{{{region_filter}}})',
            "total_servers": f'count(noc_server_up{{{region_filter}}})',
            "healthy_servers": f'sum(noc_server_up{{{region_filter}}})',
            "db_active": f'sum(noc_db_connections_active{{{region_filter}}})',
            "db_max": f'sum(noc_db_connections_max{{{region_filter}}})',
            "db_latency": f'avg(noc_db_query_latency_seconds{{{region_filter}}}) * 1000',
            "db_lag": f'avg(noc_db_replication_lag_seconds{{{region_filter}}}) * 1000',
        }

        results = {}
        for key, query in queries.items():
            try:
                result = await self.query(query)
                results[key] = self._extract_value(result)
            except Exception:
                results[key] = 0.0

        return InfrastructureMetrics(
            avg_cpu_usage=results["cpu"],
            avg_memory_usage=results["memory"],
            avg_disk_usage=results["disk"],
            total_servers=int(results["total_servers"]),
            healthy_servers=int(results["healthy_servers"]),
            db_connections_active=int(results["db_active"]),
            db_connections_max=int(results["db_max"]) or 100,
            db_avg_query_latency_ms=results["db_latency"],
            db_replication_lag_ms=results["db_lag"]
        )

    async def get_metrics_summary(self) -> MetricsSummary:
        """Get complete metrics summary for all regions."""
        regions = settings.SUPPORTED_REGIONS
        region_metrics = []

        # Get per-region metrics
        for region in regions:
            try:
                transactions = await self.get_transaction_metrics(region)
                network = await self.get_network_metrics(region)
                infrastructure = await self.get_infrastructure_metrics(region)

                region_metrics.append(RegionMetrics(
                    region=region,
                    transactions=transactions,
                    network=network,
                    infrastructure=infrastructure
                ))
            except Exception as e:
                logger.error(f"Failed to get metrics for region {region}", error=str(e))

        # Get global metrics
        global_transactions = await self.get_transaction_metrics()
        global_network = await self.get_network_metrics()
        global_infrastructure = await self.get_infrastructure_metrics()

        return MetricsSummary(
            global_transactions=global_transactions,
            global_network=global_network,
            global_infrastructure=global_infrastructure,
            regions=region_metrics
        )


# Singleton instance
prometheus_service = PrometheusService()
