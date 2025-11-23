#!/usr/bin/env python3
"""
NexusGuard NOC - Sample Data Generator

Generates realistic sample metrics for demonstration and testing.
Simulates transaction metrics, network status, and infrastructure health
across India, China, and USA regions.
"""

import time
import random
import math
from datetime import datetime
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    push_to_gateway,
)

# Configuration
PUSHGATEWAY_URL = "pushgateway:9091"
JOB_NAME = "nexusguard_sample_data"
PUSH_INTERVAL = 15  # seconds

# Create a registry
registry = CollectorRegistry()

# Define metrics
# Transaction metrics
transactions_total = Counter(
    'noc_transactions_total',
    'Total number of transactions',
    ['region', 'status'],
    registry=registry
)

transaction_latency = Histogram(
    'noc_transaction_latency',
    'Transaction latency in seconds',
    ['region'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
    registry=registry
)

hash_mismatch_total = Counter(
    'noc_hash_mismatch_total',
    'Total hash mismatches detected',
    ['region'],
    registry=registry
)

blockchain_failures_total = Counter(
    'noc_blockchain_failures_total',
    'Total blockchain commit failures',
    ['region'],
    registry=registry
)

# Network metrics
device_up = Gauge(
    'noc_device_up',
    'Whether device is up (1) or down (0)',
    ['region', 'device'],
    registry=registry
)

interface_utilization = Gauge(
    'noc_interface_utilization',
    'Interface utilization percentage',
    ['region', 'device', 'interface'],
    registry=registry
)

interface_errors_total = Counter(
    'noc_interface_errors_total',
    'Total interface errors',
    ['region', 'device'],
    registry=registry
)

interface_drops_total = Counter(
    'noc_interface_drops_total',
    'Total packet drops',
    ['region', 'device'],
    registry=registry
)

firewall_accepts_total = Counter(
    'noc_firewall_accepts_total',
    'Firewall accepted connections',
    ['region'],
    registry=registry
)

firewall_denies_total = Counter(
    'noc_firewall_denies_total',
    'Firewall denied connections',
    ['region'],
    registry=registry
)

# Infrastructure metrics
server_up = Gauge(
    'noc_server_up',
    'Whether server is up',
    ['region', 'instance'],
    registry=registry
)

server_cpu_usage = Gauge(
    'noc_server_cpu_usage',
    'Server CPU usage percentage',
    ['region', 'instance'],
    registry=registry
)

server_memory_usage = Gauge(
    'noc_server_memory_usage',
    'Server memory usage percentage',
    ['region', 'instance'],
    registry=registry
)

server_disk_usage = Gauge(
    'noc_server_disk_usage',
    'Server disk usage percentage',
    ['region', 'instance'],
    registry=registry
)

db_connections_active = Gauge(
    'noc_db_connections_active',
    'Active database connections',
    ['region'],
    registry=registry
)

db_connections_max = Gauge(
    'noc_db_connections_max',
    'Maximum database connections',
    ['region'],
    registry=registry
)

db_query_latency = Gauge(
    'noc_db_query_latency_seconds',
    'Average database query latency',
    ['region'],
    registry=registry
)

db_replication_lag = Gauge(
    'noc_db_replication_lag_seconds',
    'Database replication lag',
    ['region'],
    registry=registry
)

# Regions configuration
REGIONS = ['india', 'china', 'usa']
DEVICES_PER_REGION = ['fw-1', 'sw-1', 'sw-2', 'rt-1']
SERVERS_PER_REGION = ['app-1', 'app-2', 'db-1']


def generate_metrics():
    """Generate sample metrics for all regions."""
    current_time = time.time()
    hour_of_day = datetime.now().hour

    for region in REGIONS:
        # Regional characteristics
        if region == 'india':
            base_tps = 150
            error_rate = 0.02
            latency_base = 0.08
        elif region == 'china':
            base_tps = 200
            error_rate = 0.015
            latency_base = 0.06
        else:  # usa
            base_tps = 180
            error_rate = 0.018
            latency_base = 0.05

        # Add time-based variation (business hours)
        time_factor = 1 + 0.3 * math.sin(hour_of_day * math.pi / 12)
        tps = base_tps * time_factor

        # Generate transactions
        success_count = int(tps * (1 - error_rate) * PUSH_INTERVAL)
        failure_count = int(tps * error_rate * PUSH_INTERVAL)

        transactions_total.labels(region=region, status='success').inc(success_count)
        transactions_total.labels(region=region, status='failure').inc(failure_count)

        # Generate latencies
        for _ in range(int(tps)):
            latency = latency_base * (1 + random.gauss(0, 0.3))
            latency = max(0.001, latency)
            transaction_latency.labels(region=region).observe(latency)

        # Occasional blockchain issues
        if random.random() < 0.001:
            blockchain_failures_total.labels(region=region).inc()

        if random.random() < 0.0001:
            hash_mismatch_total.labels(region=region).inc()

        # Network devices
        for device in DEVICES_PER_REGION:
            # Most devices are up
            is_up = 1 if random.random() > 0.01 else 0
            device_up.labels(region=region, device=device).set(is_up)

            # Interface utilization
            utilization = random.gauss(45, 15)
            utilization = max(0, min(100, utilization))
            interface_utilization.labels(
                region=region, device=device, interface='eth0'
            ).set(utilization)

            # Occasional errors
            if random.random() < 0.1:
                interface_errors_total.labels(region=region, device=device).inc()
            if random.random() < 0.05:
                interface_drops_total.labels(region=region, device=device).inc()

        # Firewall metrics
        firewall_accepts_total.labels(region=region).inc(int(tps * 1.5))
        firewall_denies_total.labels(region=region).inc(int(tps * 0.02))

        # Server metrics
        for server in SERVERS_PER_REGION:
            server_up.labels(region=region, instance=server).set(1)

            cpu = random.gauss(55, 20)
            cpu = max(5, min(95, cpu))
            server_cpu_usage.labels(region=region, instance=server).set(cpu)

            memory = random.gauss(65, 15)
            memory = max(20, min(95, memory))
            server_memory_usage.labels(region=region, instance=server).set(memory)

            disk = random.gauss(50, 10)
            disk = max(20, min(90, disk))
            server_disk_usage.labels(region=region, instance=server).set(disk)

        # Database metrics
        db_connections_max.labels(region=region).set(100)
        active_conns = int(random.gauss(40, 10))
        active_conns = max(5, min(95, active_conns))
        db_connections_active.labels(region=region).set(active_conns)

        query_latency = random.gauss(0.02, 0.005)
        query_latency = max(0.001, query_latency)
        db_query_latency.labels(region=region).set(query_latency)

        repl_lag = random.gauss(0.5, 0.2)
        repl_lag = max(0, repl_lag)
        db_replication_lag.labels(region=region).set(repl_lag)


def main():
    """Main loop to generate and push metrics."""
    print(f"Starting NexusGuard NOC Data Generator")
    print(f"Pushing to: {PUSHGATEWAY_URL}")
    print(f"Interval: {PUSH_INTERVAL}s")

    while True:
        try:
            generate_metrics()
            push_to_gateway(
                PUSHGATEWAY_URL,
                job=JOB_NAME,
                registry=registry
            )
            print(f"[{datetime.now().isoformat()}] Metrics pushed successfully")
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Error: {e}")

        time.sleep(PUSH_INTERVAL)


if __name__ == '__main__':
    main()
