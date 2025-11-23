'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import MetricCard from '@/components/MetricCard';
import IncidentList from '@/components/IncidentList';
import RegionSelector from '@/components/RegionSelector';
import { metricsApi, incidentsApi } from '@/lib/api';
import { formatNumber, formatLatency, formatPercentage } from '@/lib/utils';
import type { MetricsSummary, Incident } from '@/types';
import {
  ServerIcon,
  SignalIcon,
  ExclamationTriangleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metricsData, incidentsData] = await Promise.all([
          metricsApi.getSummary(),
          incidentsApi.list({ status: 'open', limit: 10 }),
        ]);
        setMetrics(metricsData);
        setIncidents(incidentsData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
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

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">NOC Dashboard</h1>
            <p className="text-sm text-gray-500">
              Real-time monitoring across all regions
            </p>
          </div>
          <div className="w-48">
            <RegionSelector value={selectedRegion} onChange={setSelectedRegion} />
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Transactions/sec"
            value={formatNumber(txMetrics?.transactions_per_second || 0, 1)}
            subtitle={`${formatNumber(txMetrics?.total_count || 0)} total`}
            icon={<ServerIcon className="h-5 w-5" />}
          />
          <MetricCard
            title="Success Rate"
            value={formatPercentage(txMetrics?.success_rate || 0)}
            subtitle={`${txMetrics?.failure_count || 0} failures`}
            trend={txMetrics && txMetrics.success_rate >= 99 ? 'up' : 'down'}
            trendValue={txMetrics && txMetrics.success_rate >= 99 ? 'Healthy' : 'Degraded'}
            icon={<SignalIcon className="h-5 w-5" />}
          />
          <MetricCard
            title="P95 Latency"
            value={formatLatency(txMetrics?.p95_latency_ms || 0)}
            subtitle={`P99: ${formatLatency(txMetrics?.p99_latency_ms || 0)}`}
            icon={<ClockIcon className="h-5 w-5" />}
          />
          <MetricCard
            title="Open Incidents"
            value={incidents.length}
            subtitle={`${incidents.filter((i) => i.severity === 'critical').length} critical`}
            icon={<ExclamationTriangleIcon className="h-5 w-5" />}
          />
        </div>

        {/* Infrastructure & Network */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* Infrastructure */}
          <div className="rounded-lg bg-white p-6 shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Infrastructure Health</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">CPU Usage</span>
                  <span className="font-medium">{formatPercentage(infraMetrics?.avg_cpu_usage || 0)}</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full"
                    style={{ width: `${infraMetrics?.avg_cpu_usage || 0}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">Memory Usage</span>
                  <span className="font-medium">{formatPercentage(infraMetrics?.avg_memory_usage || 0)}</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full"
                    style={{ width: `${infraMetrics?.avg_memory_usage || 0}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">Disk Usage</span>
                  <span className="font-medium">{formatPercentage(infraMetrics?.avg_disk_usage || 0)}</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full"
                    style={{ width: `${infraMetrics?.avg_disk_usage || 0}%` }}
                  />
                </div>
              </div>
              <div className="pt-2 border-t">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Healthy Servers</span>
                  <span className="font-medium">
                    {infraMetrics?.healthy_servers || 0} / {infraMetrics?.total_servers || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Network */}
          <div className="rounded-lg bg-white p-6 shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Network Status</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-semibold text-green-600">
                  {netMetrics?.devices_up || 0}
                </p>
                <p className="text-sm text-gray-500">Devices Up</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-semibold text-red-600">
                  {netMetrics?.devices_down || 0}
                </p>
                <p className="text-sm text-gray-500">Devices Down</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-semibold text-gray-900">
                  {formatPercentage(netMetrics?.avg_interface_utilization || 0)}
                </p>
                <p className="text-sm text-gray-500">Interface Util</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-2xl font-semibold text-gray-900">
                  {formatNumber(netMetrics?.firewall_denies || 0)}
                </p>
                <p className="text-sm text-gray-500">FW Denies</p>
              </div>
            </div>
          </div>
        </div>

        {/* Open Incidents */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Open Incidents</h3>
            <a href="/incidents" className="text-sm text-primary-600 hover:text-primary-700">
              View all →
            </a>
          </div>
          <IncidentList incidents={incidents} />
        </div>
      </div>
    </Layout>
  );
}
