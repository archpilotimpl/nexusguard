'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import IncidentList from '@/components/IncidentList';
import { incidentsApi } from '@/lib/api';
import type { Incident, IncidentSeverity, IncidentStatus } from '@/types';

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: '' as IncidentStatus | '',
    severity: '' as IncidentSeverity | '',
    region: '',
  });

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const data = await incidentsApi.list({
          status: filters.status || undefined,
          severity: filters.severity || undefined,
          region: filters.region || undefined,
          limit: 100,
        });
        setIncidents(data);
      } catch (error) {
        console.error('Failed to fetch incidents:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchIncidents();
  }, [filters]);

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Incidents</h1>
        </div>

        {/* Filters */}
        <div className="flex gap-4 flex-wrap">
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value as IncidentStatus })}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">All Status</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>

          <select
            value={filters.severity}
            onChange={(e) => setFilters({ ...filters, severity: e.target.value as IncidentSeverity })}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">All Severity</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={filters.region}
            onChange={(e) => setFilters({ ...filters, region: e.target.value })}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">All Regions</option>
            <option value="india">India</option>
            <option value="china">China</option>
            <option value="usa">USA</option>
          </select>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent"></div>
          </div>
        ) : (
          <IncidentList incidents={incidents} />
        )}
      </div>
    </Layout>
  );
}
