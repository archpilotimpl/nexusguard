'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import RegionSelector from '@/components/RegionSelector';
import { metricsApi } from '@/lib/api';
import { formatNumber, formatLatency, formatPercentage } from '@/lib/utils';
import type { MetricsSummary } from '@/types';

// Grafana dashboard configuration
const GRAFANA_URL = process.env.NEXT_PUBLIC_GRAFANA_URL || 'http://localhost:3001';
const GRAFANA_DASHBOARD_ID = 'noc-overview';

interface GrafanaPanelProps {
  panelId: number;
  title: string;
  height?: number;
  from?: string;
  to?: string;
}

function GrafanaPanel({ panelId, title, height = 200, from = 'now-1h', to = 'now' }: GrafanaPanelProps) {
  const panelUrl = `${GRAFANA_URL}/d-solo/${GRAFANA_DASHBOARD_ID}?orgId=1&panelId=${panelId}&from=${from}&to=${to}&theme=light`;

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100">
        <h4 className="text-sm font-medium text-gray-700">{title}</h4>
      </div>
      <iframe
        src={panelUrl}
        width="100%"
        height={height}
        frameBorder="0"
        className="bg-gray-50"
      />
    </div>
  );
}

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: 'default' | 'green' | 'red' | 'yellow';
  trend?: 'up' | 'down' | 'stable';
}

function MetricCard({ title, value, subtitle, color = 'default', trend }: MetricCardProps) {
  const colorClasses = {
    default: 'text-gray-900',
    green: 'text-green-600',
    red: 'text-red-600',
    yellow: 'text-yellow-600',
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-sm text-gray-500">{title}</p>
      <div className="flex items-baseline gap-2">
        <p className={`text-2xl font-semibold ${colorClasses[color]}`}>{value}</p>
        {trend && (
          <span className={`text-sm ${trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-gray-400'}`}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
          </span>
        )}
      </div>
      {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
    </div>
  );
}

// Simple chart component for when Grafana isn't available
function SimpleBarChart({ data, label }: { data: number[]; label: string }) {
  const max = Math.max(...data, 1);

  return (
    <div className="h-24 flex items-end gap-1">
      {data.map((value, i) => (
        <div
          key={i}
          className="flex-1 bg-primary-500 rounded-t opacity-80 hover:opacity-100 transition-opacity"
          style={{ height: `${(value / max) * 100}%` }}
          title={`${label}: ${value}`}
        />
      ))}
    </div>
  );
}

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showGrafana, setShowGrafana] = useState(false);
  const [timeRange, setTimeRange] = useState('1h');

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await metricsApi.getSummary();
        setMetrics(data);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent"></div>
        </div>
      </Layout>
    );
  }

  const currentMetrics = selectedRegion
    ? metrics?.regions.find((r) => r.region === selectedRegion)
    : null;

  const txMetrics = currentMetrics?.transactions || metrics?.global_transactions;
  const netMetrics = currentMetrics?.network || metrics?.global_network;
  const infraMetrics = currentMetrics?.infrastructure || metrics?.global_infrastructure;

  const timeRangeOptions = [
    { value: '15m', label: '15m' },
    { value: '1h', label: '1h' },
    { value: '6h', label: '6h' },
    { value: '24h', label: '24h' },
    { value: '7d', label: '7d' },
  ];

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Metrics</h1>
          <div className="flex items-center gap-4">
            {/* Time Range Selector */}
            <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
              {timeRangeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setTimeRange(option.value)}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    timeRange === option.value
                      ? 'bg-white shadow text-primary-600 font-medium'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>

            {/* Grafana Toggle */}
            <button
              onClick={() => setShowGrafana(!showGrafana)}
              className={`px-3 py-1.5 text-sm rounded-md border ${
                showGrafana
                  ? 'bg-primary-50 border-primary-200 text-primary-700'
                  : 'bg-white border-gray-300 text-gray-600'
              }`}
            >
              {showGrafana ? 'Grafana On' : 'Grafana Off'}
            </button>

            <div className="w-48">
              <RegionSelector value={selectedRegion} onChange={setSelectedRegion} />
            </div>
          </div>
        </div>

        {/* Reliability Thresholds (SLOs/SLIs) */}
        <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 mt-1">
              <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Recommended Reliability Thresholds (SLOs)
              </h3>
              <p className="text-sm text-gray-700 mb-4">
                Service Level Objectives (SLOs) and Service Level Indicators (SLIs) define the target reliability
                metrics for NexusGuard NOC. These thresholds are based on industry best practices for high-volume
                transaction processing systems handling 30-50M transactions/month.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Transaction Reliability */}
                <div className="bg-white rounded-lg p-4 border border-green-100">
                  <h4 className="text-sm font-semibold text-gray-800 mb-2">Transaction Reliability</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Success Rate:</span>
                      <span className="font-mono font-medium text-green-700">≥ 99.9%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Error Rate:</span>
                      <span className="font-mono font-medium text-green-700">≤ 0.1%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Hash Mismatch:</span>
                      <span className="font-mono font-medium text-green-700">≤ 0.01%</span>
                    </div>
                    <p className="text-gray-500 italic mt-2 pt-2 border-t border-gray-100">
                      Three nines availability ensures reliable transaction processing
                    </p>
                  </div>
                </div>

                {/* Latency Performance */}
                <div className="bg-white rounded-lg p-4 border border-blue-100">
                  <h4 className="text-sm font-semibold text-gray-800 mb-2">Latency Performance</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">P50 Latency:</span>
                      <span className="font-mono font-medium text-blue-700">≤ 200ms</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">P95 Latency:</span>
                      <span className="font-mono font-medium text-blue-700">≤ 500ms</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">P99 Latency:</span>
                      <span className="font-mono font-medium text-blue-700">≤ 1000ms</span>
                    </div>
                    <p className="text-gray-500 italic mt-2 pt-2 border-t border-gray-100">
                      Sub-second response for 99% of transactions
                    </p>
                  </div>
                </div>

                {/* Infrastructure Health */}
                <div className="bg-white rounded-lg p-4 border border-purple-100">
                  <h4 className="text-sm font-semibold text-gray-800 mb-2">Infrastructure Health</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">CPU Usage:</span>
                      <span className="font-mono font-medium text-purple-700">≤ 80%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Memory Usage:</span>
                      <span className="font-mono font-medium text-purple-700">≤ 85%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Disk Usage:</span>
                      <span className="font-mono font-medium text-purple-700">≤ 80%</span>
                    </div>
                    <p className="text-gray-500 italic mt-2 pt-2 border-t border-gray-100">
                      Headroom for burst capacity and maintenance
                    </p>
                  </div>
                </div>

                {/* Firewall Security */}
                <div className="bg-white rounded-lg p-4 border border-orange-100">
                  <h4 className="text-sm font-semibold text-gray-800 mb-2">Firewall Security</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Availability:</span>
                      <span className="font-mono font-medium text-orange-700">≥ 99.95%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Session Utilization:</span>
                      <span className="font-mono font-medium text-orange-700">≤ 75%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Deny Rate:</span>
                      <span className="font-mono font-medium text-orange-700">≤ 5%</span>
                    </div>
                    <p className="text-gray-500 italic mt-2 pt-2 border-t border-gray-100">
                      High firewall availability with threat blocking capacity
                    </p>
                  </div>
                </div>

                {/* Layer 3 Routing */}
                <div className="bg-white rounded-lg p-4 border border-blue-100">
                  <h4 className="text-sm font-semibold text-gray-800 mb-2">Layer 3 Routing</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">BGP Sessions:</span>
                      <span className="font-mono font-medium text-blue-700">100% Up</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">OSPF Neighbors:</span>
                      <span className="font-mono font-medium text-blue-700">100% Full</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Packet Drop Rate:</span>
                      <span className="font-mono font-medium text-blue-700">≤ 0.01%</span>
                    </div>
                    <p className="text-gray-500 italic mt-2 pt-2 border-t border-gray-100">
                      Stable routing protocols ensure network convergence
                    </p>
                  </div>
                </div>

                {/* Layer 4 Load Balancing */}
                <div className="bg-white rounded-lg p-4 border border-purple-100">
                  <h4 className="text-sm font-semibold text-gray-800 mb-2">Layer 4 Load Balancing</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Backend Health:</span>
                      <span className="font-mono font-medium text-purple-700">≥ 95%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">SSL TPS:</span>
                      <span className="font-mono font-medium text-purple-700">≥ 1000/s</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Connection Utilization:</span>
                      <span className="font-mono font-medium text-purple-700">≤ 80%</span>
                    </div>
                    <p className="text-gray-500 italic mt-2 pt-2 border-t border-gray-100">
                      Healthy backends with SSL/TLS processing capacity
                    </p>
                  </div>
                </div>

                {/* Network Performance */}
                <div className="bg-white rounded-lg p-4 border border-cyan-100">
                  <h4 className="text-sm font-semibold text-gray-800 mb-2">Network Performance</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Device Availability:</span>
                      <span className="font-mono font-medium text-cyan-700">≥ 99.95%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Interface Utilization:</span>
                      <span className="font-mono font-medium text-cyan-700">≤ 75%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Error Rate:</span>
                      <span className="font-mono font-medium text-cyan-700">≤ 0.1%</span>
                    </div>
                    <p className="text-gray-500 italic mt-2 pt-2 border-t border-gray-100">
                      High network reliability across all regions
                    </p>
                  </div>
                </div>

                {/* Database Performance */}
                <div className="bg-white rounded-lg p-4 border border-teal-100">
                  <h4 className="text-sm font-semibold text-gray-800 mb-2">Database Performance</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Query Latency:</span>
                      <span className="font-mono font-medium text-teal-700">≤ 50ms</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Replication Lag:</span>
                      <span className="font-mono font-medium text-teal-700">≤ 100ms</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Connection Pool:</span>
                      <span className="font-mono font-medium text-teal-700">≤ 80%</span>
                    </div>
                    <p className="text-gray-500 italic mt-2 pt-2 border-t border-gray-100">
                      Fast data access with minimal replication delay
                    </p>
                  </div>
                </div>

                {/* Disaster Recovery */}
                <div className="bg-white rounded-lg p-4 border border-red-100">
                  <h4 className="text-sm font-semibold text-gray-800 mb-2">Business Continuity</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">RTO (Recovery Time):</span>
                      <span className="font-mono font-medium text-red-700">≤ 4 hours</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">RPO (Data Loss):</span>
                      <span className="font-mono font-medium text-red-700">≤ 15 minutes</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Backup Success:</span>
                      <span className="font-mono font-medium text-red-700">100%</span>
                    </div>
                    <p className="text-gray-500 italic mt-2 pt-2 border-t border-gray-100">
                      Compliance with GENIUS Act 3.1 requirements
                    </p>
                  </div>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-green-200">
                <p className="text-xs text-gray-600">
                  <strong>Note:</strong> These thresholds align with industry-standard SLOs for financial transaction
                  processing systems and regulatory requirements (GENIUS Act 2025, PCI-DSS v4.0). Current metrics are
                  color-coded: <span className="text-green-600 font-medium">Green</span> = within threshold,
                  <span className="text-yellow-600 font-medium">Yellow</span> = warning,
                  <span className="text-red-600 font-medium">Red</span> = critical.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <MetricCard
            title="Transactions/sec"
            value={formatNumber(txMetrics?.transactions_per_second || 0, 1)}
            subtitle="Current TPS"
          />
          <MetricCard
            title="Success Rate"
            value={formatPercentage(txMetrics?.success_rate || 0)}
            color={(txMetrics?.success_rate || 0) >= 99 ? 'green' : (txMetrics?.success_rate || 0) >= 95 ? 'yellow' : 'red'}
          />
          <MetricCard
            title="Error Rate"
            value={formatPercentage(txMetrics?.error_rate || 0)}
            color={(txMetrics?.error_rate || 0) <= 1 ? 'green' : (txMetrics?.error_rate || 0) <= 5 ? 'yellow' : 'red'}
          />
          <MetricCard
            title="P99 Latency"
            value={formatLatency(txMetrics?.p99_latency_ms || 0)}
            color={(txMetrics?.p99_latency_ms || 0) <= 500 ? 'green' : (txMetrics?.p99_latency_ms || 0) <= 1000 ? 'yellow' : 'red'}
          />
          <MetricCard
            title="CPU Usage"
            value={formatPercentage(infraMetrics?.avg_cpu_usage || 0)}
            color={(infraMetrics?.avg_cpu_usage || 0) <= 70 ? 'green' : (infraMetrics?.avg_cpu_usage || 0) <= 85 ? 'yellow' : 'red'}
          />
          <MetricCard
            title="Memory Usage"
            value={formatPercentage(infraMetrics?.avg_memory_usage || 0)}
            color={(infraMetrics?.avg_memory_usage || 0) <= 70 ? 'green' : (infraMetrics?.avg_memory_usage || 0) <= 85 ? 'yellow' : 'red'}
          />
        </div>

        {/* Grafana Panels */}
        {showGrafana && (
          <div className="space-y-4">
            <h2 className="text-lg font-medium text-gray-900">Grafana Dashboards</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <GrafanaPanel
                panelId={1}
                title="Transaction Rate"
                height={250}
                from={`now-${timeRange}`}
              />
              <GrafanaPanel
                panelId={2}
                title="Error Rate by Region"
                height={250}
                from={`now-${timeRange}`}
              />
              <GrafanaPanel
                panelId={3}
                title="Latency Percentiles"
                height={250}
                from={`now-${timeRange}`}
              />
              <GrafanaPanel
                panelId={4}
                title="Network Device Status"
                height={250}
                from={`now-${timeRange}`}
              />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <GrafanaPanel
                panelId={5}
                title="CPU Usage by Server"
                height={200}
                from={`now-${timeRange}`}
              />
              <GrafanaPanel
                panelId={6}
                title="Memory Usage"
                height={200}
                from={`now-${timeRange}`}
              />
              <GrafanaPanel
                panelId={7}
                title="Disk Usage"
                height={200}
                from={`now-${timeRange}`}
              />
            </div>
            <p className="text-xs text-gray-500 text-center">
              Grafana panels require Grafana to be running at {GRAFANA_URL}.
              <a href={GRAFANA_URL} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline ml-1">
                Open Grafana Dashboard
              </a>
            </p>
          </div>
        )}

        {/* Transaction Metrics Detail */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Transaction Details</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Total Transactions</p>
              <p className="text-2xl font-semibold">{formatNumber(txMetrics?.total_count || 0)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Successful</p>
              <p className="text-2xl font-semibold text-green-600">{formatNumber(txMetrics?.success_count || 0)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Failed</p>
              <p className="text-2xl font-semibold text-red-600">{formatNumber(txMetrics?.failure_count || 0)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Hash Mismatches</p>
              <p className="text-2xl font-semibold text-yellow-600">{formatNumber(txMetrics?.hash_mismatch_count || 0)}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t">
            <div>
              <p className="text-sm text-gray-500">Avg Latency</p>
              <p className="text-lg font-medium">{formatLatency(txMetrics?.avg_latency_ms || 0)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">P50 Latency</p>
              <p className="text-lg font-medium">{formatLatency(txMetrics?.p50_latency_ms || 0)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">P95 Latency</p>
              <p className="text-lg font-medium">{formatLatency(txMetrics?.p95_latency_ms || 0)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Blockchain Failures</p>
              <p className="text-lg font-medium text-red-600">{formatNumber(txMetrics?.blockchain_failures || 0)}</p>
            </div>
          </div>
        </div>

        {/* Network Metrics Overview */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Network Infrastructure Overview</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <div>
              <p className="text-sm text-gray-500">Total Devices</p>
              <p className="text-2xl font-semibold">{netMetrics?.devices_total || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Devices Up</p>
              <p className="text-2xl font-semibold text-green-600">{netMetrics?.devices_up || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Devices Down</p>
              <p className="text-2xl font-semibold text-red-600">{netMetrics?.devices_down || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Interface Util</p>
              <p className="text-2xl font-semibold">{formatPercentage(netMetrics?.avg_interface_utilization || 0)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Errors</p>
              <p className="text-2xl font-semibold text-yellow-600">{formatNumber(netMetrics?.total_errors || 0)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Drops</p>
              <p className="text-2xl font-semibold text-yellow-600">{formatNumber(netMetrics?.total_drops || 0)}</p>
            </div>
          </div>
        </div>

        {/* Firewall Metrics (Layer 7) */}
        {netMetrics?.firewall && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <svg className="h-5 w-5 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900">Firewall Security Metrics</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <div>
                <p className="text-sm text-gray-500">Active Firewalls</p>
                <p className="text-2xl font-semibold">
                  <span className="text-green-600">{netMetrics.firewall.firewalls_up}</span>
                  <span className="text-gray-400 text-lg"> / {netMetrics.firewall.total_firewalls}</span>
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Accepts/sec</p>
                <p className="text-2xl font-semibold text-green-600">{formatNumber(netMetrics.firewall.accepts_per_second, 1)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Denies/sec</p>
                <p className="text-2xl font-semibold text-red-600">{formatNumber(netMetrics.firewall.denies_per_second, 1)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Deny Rate</p>
                <p className="text-2xl font-semibold text-orange-600">{formatPercentage(netMetrics.firewall.deny_rate)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Threats Blocked</p>
                <p className="text-2xl font-semibold text-red-600">{formatNumber(netMetrics.firewall.blocked_threats)}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mt-4 pt-4 border-t">
              <div>
                <p className="text-sm text-gray-500">Active Sessions</p>
                <p className="text-lg font-medium">{formatNumber(netMetrics.firewall.sessions_active)}</p>
                <p className="text-xs text-gray-400">of {formatNumber(netMetrics.firewall.sessions_max)} max</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">CPU Usage</p>
                <p className="text-lg font-medium">{formatPercentage(netMetrics.firewall.cpu_usage)}</p>
                <div className="mt-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      netMetrics.firewall.cpu_usage <= 70 ? 'bg-green-500' : netMetrics.firewall.cpu_usage <= 85 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${netMetrics.firewall.cpu_usage}%` }}
                  />
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500">Memory Usage</p>
                <p className="text-lg font-medium">{formatPercentage(netMetrics.firewall.memory_usage)}</p>
                <div className="mt-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      netMetrics.firewall.memory_usage <= 70 ? 'bg-green-500' : netMetrics.firewall.memory_usage <= 85 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${netMetrics.firewall.memory_usage}%` }}
                  />
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500">Throughput</p>
                <p className="text-lg font-medium">{formatNumber(netMetrics.firewall.throughput_mbps, 1)} Mbps</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">VPN Tunnels</p>
                <p className="text-lg font-medium text-blue-600">{netMetrics.firewall.vpn_tunnels_active}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Accepts</p>
                <p className="text-lg font-medium text-green-600">{formatNumber(netMetrics.firewall.total_accepts)}</p>
              </div>
            </div>
          </div>
        )}

        {/* Layer 3 Router Metrics */}
        {netMetrics?.layer3 && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <svg className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900">Layer 3 Router Metrics (BGP & OSPF)</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <div>
                <p className="text-sm text-gray-500">Active Routers</p>
                <p className="text-2xl font-semibold">
                  <span className="text-green-600">{netMetrics.layer3.routers_up}</span>
                  <span className="text-gray-400 text-lg"> / {netMetrics.layer3.total_routers}</span>
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">BGP Sessions</p>
                <p className="text-2xl font-semibold">
                  <span className={netMetrics.layer3.bgp_sessions_established === netMetrics.layer3.bgp_sessions_total ? 'text-green-600' : 'text-yellow-600'}>
                    {netMetrics.layer3.bgp_sessions_established}
                  </span>
                  <span className="text-gray-400 text-lg"> / {netMetrics.layer3.bgp_sessions_total}</span>
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">OSPF Neighbors</p>
                <p className="text-2xl font-semibold">
                  <span className={netMetrics.layer3.ospf_neighbors_full === netMetrics.layer3.ospf_neighbors_total ? 'text-green-600' : 'text-yellow-600'}>
                    {netMetrics.layer3.ospf_neighbors_full}
                  </span>
                  <span className="text-gray-400 text-lg"> / {netMetrics.layer3.ospf_neighbors_total}</span>
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Routes</p>
                <p className="text-2xl font-semibold text-blue-600">{formatNumber(netMetrics.layer3.routes_total)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Packets Forwarded</p>
                <p className="text-2xl font-semibold text-green-600">{formatNumber(netMetrics.layer3.packets_forwarded)}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mt-4 pt-4 border-t">
              <div>
                <p className="text-sm text-gray-500">BGP Routes</p>
                <p className="text-lg font-medium text-blue-600">{formatNumber(netMetrics.layer3.routes_bgp)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">OSPF Routes</p>
                <p className="text-lg font-medium text-green-600">{formatNumber(netMetrics.layer3.routes_ospf)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Static Routes</p>
                <p className="text-lg font-medium text-gray-600">{formatNumber(netMetrics.layer3.routes_static)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Packets Dropped</p>
                <p className="text-lg font-medium text-red-600">{formatNumber(netMetrics.layer3.packets_dropped)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">CPU Usage</p>
                <p className="text-lg font-medium">{formatPercentage(netMetrics.layer3.cpu_usage)}</p>
                <div className="mt-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      netMetrics.layer3.cpu_usage <= 70 ? 'bg-green-500' : netMetrics.layer3.cpu_usage <= 85 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${netMetrics.layer3.cpu_usage}%` }}
                  />
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500">Memory Usage</p>
                <p className="text-lg font-medium">{formatPercentage(netMetrics.layer3.memory_usage)}</p>
                <div className="mt-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      netMetrics.layer3.memory_usage <= 70 ? 'bg-green-500' : netMetrics.layer3.memory_usage <= 85 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${netMetrics.layer3.memory_usage}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Layer 4 Load Balancer Metrics */}
        {netMetrics?.layer4 && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              <svg className="h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900">Layer 4 Load Balancer Metrics (SSL/TLS)</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <div>
                <p className="text-sm text-gray-500">Active Load Balancers</p>
                <p className="text-2xl font-semibold">
                  <span className="text-green-600">{netMetrics.layer4.load_balancers_up}</span>
                  <span className="text-gray-400 text-lg"> / {netMetrics.layer4.total_load_balancers}</span>
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Active Connections</p>
                <p className="text-2xl font-semibold text-blue-600">{formatNumber(netMetrics.layer4.active_connections)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Connections/sec</p>
                <p className="text-2xl font-semibold text-green-600">{formatNumber(netMetrics.layer4.connections_per_second, 1)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">SSL TPS</p>
                <p className="text-2xl font-semibold text-purple-600">{formatNumber(netMetrics.layer4.ssl_tps, 1)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Bandwidth</p>
                <p className="text-2xl font-semibold text-blue-600">{formatNumber(netMetrics.layer4.total_bandwidth_mbps, 1)} Mbps</p>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mt-4 pt-4 border-t">
              <div>
                <p className="text-sm text-gray-500">Backend Servers</p>
                <p className="text-lg font-medium">
                  <span className={netMetrics.layer4.backend_servers_healthy === netMetrics.layer4.backend_servers_total ? 'text-green-600' : 'text-yellow-600'}>
                    {netMetrics.layer4.backend_servers_healthy}
                  </span>
                  <span className="text-gray-400"> / {netMetrics.layer4.backend_servers_total}</span>
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Health Check Failures</p>
                <p className="text-lg font-medium text-red-600">{netMetrics.layer4.health_check_failures}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">SSL Handshakes</p>
                <p className="text-lg font-medium text-purple-600">{formatNumber(netMetrics.layer4.ssl_handshakes)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Session Persistence</p>
                <p className="text-lg font-medium text-blue-600">{formatNumber(netMetrics.layer4.session_persistence_hits)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">CPU Usage</p>
                <p className="text-lg font-medium">{formatPercentage(netMetrics.layer4.cpu_usage)}</p>
                <div className="mt-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      netMetrics.layer4.cpu_usage <= 70 ? 'bg-green-500' : netMetrics.layer4.cpu_usage <= 85 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${netMetrics.layer4.cpu_usage}%` }}
                  />
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500">Memory Usage</p>
                <p className="text-lg font-medium">{formatPercentage(netMetrics.layer4.memory_usage)}</p>
                <div className="mt-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      netMetrics.layer4.memory_usage <= 70 ? 'bg-green-500' : netMetrics.layer4.memory_usage <= 85 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${netMetrics.layer4.memory_usage}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Infrastructure Metrics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Server Infrastructure</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">CPU Usage</p>
              <p className="text-2xl font-semibold">{formatPercentage(infraMetrics?.avg_cpu_usage || 0)}</p>
              <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    (infraMetrics?.avg_cpu_usage || 0) <= 70
                      ? 'bg-green-500'
                      : (infraMetrics?.avg_cpu_usage || 0) <= 85
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${infraMetrics?.avg_cpu_usage || 0}%` }}
                />
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-500">Memory Usage</p>
              <p className="text-2xl font-semibold">{formatPercentage(infraMetrics?.avg_memory_usage || 0)}</p>
              <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    (infraMetrics?.avg_memory_usage || 0) <= 70
                      ? 'bg-green-500'
                      : (infraMetrics?.avg_memory_usage || 0) <= 85
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${infraMetrics?.avg_memory_usage || 0}%` }}
                />
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-500">Disk Usage</p>
              <p className="text-2xl font-semibold">{formatPercentage(infraMetrics?.avg_disk_usage || 0)}</p>
              <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    (infraMetrics?.avg_disk_usage || 0) <= 70
                      ? 'bg-green-500'
                      : (infraMetrics?.avg_disk_usage || 0) <= 85
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${infraMetrics?.avg_disk_usage || 0}%` }}
                />
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-500">Healthy Servers</p>
              <p className="text-2xl font-semibold">
                <span className="text-green-600">{infraMetrics?.healthy_servers || 0}</span>
                <span className="text-gray-400"> / {infraMetrics?.total_servers || 0}</span>
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t">
            <div>
              <p className="text-sm text-gray-500">DB Connections Active</p>
              <p className="text-lg font-medium">{infraMetrics?.db_connections_active || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">DB Connections Max</p>
              <p className="text-lg font-medium">{infraMetrics?.db_connections_max || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">DB Query Latency</p>
              <p className="text-lg font-medium">{formatLatency(infraMetrics?.db_avg_query_latency_ms || 0)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Replication Lag</p>
              <p className={`text-lg font-medium ${
                (infraMetrics?.db_replication_lag_ms || 0) > 1000 ? 'text-red-600' : ''
              }`}>
                {formatLatency(infraMetrics?.db_replication_lag_ms || 0)}
              </p>
            </div>
          </div>
        </div>

        {/* Region Comparison */}
        {!selectedRegion && metrics?.regions && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Region Comparison</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Region</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">TPS</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Success Rate</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">P99 Latency</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">CPU</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Memory</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Devices Up</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {metrics.regions.map((region) => (
                    <tr key={region.region} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900 uppercase">{region.region}</td>
                      <td className="px-4 py-3 text-sm text-right">{formatNumber(region.transactions.transactions_per_second, 1)}</td>
                      <td className="px-4 py-3 text-sm text-right">
                        <span className={region.transactions.success_rate >= 99 ? 'text-green-600' : region.transactions.success_rate >= 95 ? 'text-yellow-600' : 'text-red-600'}>
                          {formatPercentage(region.transactions.success_rate)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-right">{formatLatency(region.transactions.p99_latency_ms)}</td>
                      <td className="px-4 py-3 text-sm text-right">{formatPercentage(region.infrastructure.avg_cpu_usage)}</td>
                      <td className="px-4 py-3 text-sm text-right">{formatPercentage(region.infrastructure.avg_memory_usage)}</td>
                      <td className="px-4 py-3 text-sm text-right">
                        <span className="text-green-600">{region.network.devices_up}</span>
                        <span className="text-gray-400"> / {region.network.devices_total}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
