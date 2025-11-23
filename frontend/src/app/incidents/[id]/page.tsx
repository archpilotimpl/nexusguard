'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Layout from '@/components/Layout';
import { incidentsApi, ansibleApi } from '@/lib/api';
import { cn, getSeverityColor, getStatusColor, timeAgo } from '@/lib/utils';
import type { Incident } from '@/types';
import toast from 'react-hot-toast';

export default function IncidentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchIncident = async () => {
      try {
        const data = await incidentsApi.get(params.id as string);
        setIncident(data);
      } catch (error) {
        console.error('Failed to fetch incident:', error);
        toast.error('Failed to load incident');
      } finally {
        setLoading(false);
      }
    };

    if (params.id) {
      fetchIncident();
    }
  }, [params.id]);

  const handleAcknowledge = async () => {
    if (!incident) return;
    try {
      const updated = await incidentsApi.acknowledge(incident.id);
      setIncident(updated);
      toast.success('Incident acknowledged');
    } catch (error) {
      toast.error('Failed to acknowledge incident');
    }
  };

  const handleResolve = async () => {
    if (!incident) return;
    try {
      const updated = await incidentsApi.resolve(incident.id);
      setIncident(updated);
      toast.success('Incident resolved');
    } catch (error) {
      toast.error('Failed to resolve incident');
    }
  };

  const handleRunPlaybook = async () => {
    if (!incident?.recommended_playbook) return;
    try {
      await ansibleApi.runPlaybook({
        playbook_id: incident.recommended_playbook,
        incident_id: incident.id,
      });
      toast.success('Playbook execution started');
    } catch (error) {
      toast.error('Failed to run playbook');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent"></div>
        </div>
      </Layout>
    );
  }

  if (!incident) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-gray-500">Incident not found</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <button
              onClick={() => router.back()}
              className="text-sm text-gray-500 hover:text-gray-700 mb-2"
            >
              ← Back to incidents
            </button>
            <h1 className="text-2xl font-bold text-gray-900">{incident.title}</h1>
            <div className="mt-2 flex items-center gap-3">
              <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-medium', getSeverityColor(incident.severity))}>
                {incident.severity.toUpperCase()}
              </span>
              <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-medium', getStatusColor(incident.status))}>
                {incident.status.replace('_', ' ')}
              </span>
              <span className="text-sm text-gray-500">
                {timeAgo(incident.created_at)}
              </span>
            </div>
          </div>

          <div className="flex gap-2">
            {incident.status === 'open' && (
              <button
                onClick={handleAcknowledge}
                className="px-4 py-2 bg-yellow-100 text-yellow-700 rounded-md text-sm font-medium hover:bg-yellow-200"
              >
                Acknowledge
              </button>
            )}
            {['open', 'acknowledged', 'in_progress'].includes(incident.status) && (
              <button
                onClick={handleResolve}
                className="px-4 py-2 bg-green-100 text-green-700 rounded-md text-sm font-medium hover:bg-green-200"
              >
                Resolve
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Description */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-medium text-gray-900 mb-3">Description</h3>
              <p className="text-gray-700">{incident.description}</p>
            </div>

            {/* Root Cause */}
            {incident.root_cause_hypothesis && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="font-medium text-gray-900 mb-3">Root Cause Hypothesis</h3>
                <p className="text-gray-700">{incident.root_cause_hypothesis}</p>
              </div>
            )}

            {/* Corrective Actions */}
            {incident.corrective_actions && incident.corrective_actions.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="font-medium text-gray-900 mb-3">Corrective Actions</h3>
                <ol className="list-decimal list-inside space-y-2">
                  {incident.corrective_actions.map((action, index) => (
                    <li key={index} className="text-gray-700">{action}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Details */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-medium text-gray-900 mb-4">Details</h3>
              <dl className="space-y-3 text-sm">
                <div>
                  <dt className="text-gray-500">Service</dt>
                  <dd className="font-medium">{incident.service}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Region</dt>
                  <dd className="font-medium capitalize">{incident.region}</dd>
                </div>
                {incident.assigned_to && (
                  <div>
                    <dt className="text-gray-500">Assigned To</dt>
                    <dd className="font-medium">{incident.assigned_to}</dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Recommended Playbook */}
            {incident.recommended_playbook && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="font-medium text-gray-900 mb-4">Recommended Playbook</h3>
                <p className="text-sm text-gray-600 mb-3">{incident.recommended_playbook}</p>
                <button
                  onClick={handleRunPlaybook}
                  className="w-full px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700"
                >
                  Run Playbook
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
