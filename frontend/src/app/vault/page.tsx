'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { vaultApi } from '@/lib/api';
import type {
  VaultSummary,
  VaultSecretPath,
  AnsibleVaultIntegration,
  VaultPolicy,
} from '@/types';
import {
  KeyIcon,
  LockClosedIcon,
  LockOpenIcon,
  ServerIcon,
  LinkIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function VaultPage() {
  const [summary, setSummary] = useState<VaultSummary | null>(null);
  const [secretPaths, setSecretPaths] = useState<VaultSecretPath[]>([]);
  const [integrations, setIntegrations] = useState<AnsibleVaultIntegration[]>([]);
  const [policies, setPolicies] = useState<VaultPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'secrets' | 'integrations' | 'policies'>('secrets');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [summaryData, pathsData, integrationsData, policiesData] = await Promise.all([
          vaultApi.getSummary(),
          vaultApi.listSecretPaths(),
          vaultApi.listAnsibleIntegrations(),
          vaultApi.listPolicies(),
        ]);
        setSummary(summaryData);
        setSecretPaths(pathsData);
        setIntegrations(integrationsData);
        setPolicies(policiesData);
      } catch (error) {
        console.error('Failed to fetch vault data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleTestConnection = async () => {
    try {
      const result = await vaultApi.testConnection();
      if (result.success) {
        toast.success(`Connected to Vault ${result.version}`);
      } else {
        toast.error(`Connection failed: ${result.error}`);
      }
    } catch (error) {
      toast.error('Failed to test connection');
    }
  };

  const getEngineIcon = (engine: string) => {
    switch (engine) {
      case 'kv-v2':
      case 'kv-v1':
        return <KeyIcon className="h-5 w-5" />;
      case 'ssh':
        return <ServerIcon className="h-5 w-5" />;
      case 'pki':
        return <ShieldCheckIcon className="h-5 w-5" />;
      default:
        return <LockClosedIcon className="h-5 w-5" />;
    }
  };

  const getEngineColor = (engine: string) => {
    const colors: Record<string, string> = {
      'kv-v2': 'bg-blue-100 text-blue-700',
      'kv-v1': 'bg-blue-100 text-blue-700',
      ssh: 'bg-green-100 text-green-700',
      pki: 'bg-purple-100 text-purple-700',
      aws: 'bg-orange-100 text-orange-700',
      database: 'bg-yellow-100 text-yellow-700',
      transit: 'bg-indigo-100 text-indigo-700',
    };
    return colors[engine] || 'bg-gray-100 text-gray-700';
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Vault Configuration</h1>
            <p className="text-sm text-gray-500 mt-1">
              HashiCorp Vault integration for secure credential management
            </p>
          </div>
          <button
            onClick={handleTestConnection}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Test Connection
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent"></div>
          </div>
        ) : (
          <>
            {/* Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-lg ${
                      summary?.sealed ? 'bg-red-100' : 'bg-green-100'
                    }`}
                  >
                    {summary?.sealed ? (
                      <LockClosedIcon className="h-6 w-6 text-red-600" />
                    ) : (
                      <LockOpenIcon className="h-6 w-6 text-green-600" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Status</p>
                    <p className="text-lg font-bold text-gray-900">
                      {summary?.status?.toUpperCase()}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <KeyIcon className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Secret Paths</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {summary?.secret_paths_count}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <LinkIcon className="h-6 w-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Ansible Integrations</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {summary?.enabled_integrations}/{summary?.ansible_integrations_count}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    <ServerIcon className="h-6 w-6 text-gray-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Version</p>
                    <p className="text-lg font-bold text-gray-900">{summary?.version}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Connection Info */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Connection Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Address</p>
                  <p className="text-sm font-mono text-gray-900">{summary?.address}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Auth Method</p>
                  <p className="text-sm font-medium text-gray-900">{summary?.auth_method}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Cluster</p>
                  <p className="text-sm font-medium text-gray-900">{summary?.cluster_name}</p>
                </div>
              </div>
              <div className="mt-4">
                <p className="text-sm text-gray-500 mb-2">Engines in Use</p>
                <div className="flex flex-wrap gap-2">
                  {summary?.engines_in_use.map((engine) => (
                    <span
                      key={engine}
                      className={`px-3 py-1 rounded-full text-xs font-medium ${getEngineColor(
                        engine
                      )}`}
                    >
                      {engine}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="bg-white rounded-lg shadow">
              <div className="border-b border-gray-200">
                <nav className="flex -mb-px">
                  <button
                    onClick={() => setActiveTab('secrets')}
                    className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'secrets'
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Secret Paths ({secretPaths.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('integrations')}
                    className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'integrations'
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Ansible Integrations ({integrations.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('policies')}
                    className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'policies'
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Policies ({policies.length})
                  </button>
                </nav>
              </div>

              <div className="p-6">
                {/* Secret Paths Tab */}
                {activeTab === 'secrets' && (
                  <div className="space-y-4">
                    {secretPaths.map((path) => (
                      <div
                        key={path.id}
                        className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <div className={`p-2 rounded-lg ${getEngineColor(path.engine)}`}>
                              {getEngineIcon(path.engine)}
                            </div>
                            <div>
                              <h4 className="font-medium text-gray-900">{path.name}</h4>
                              <p className="text-sm font-mono text-gray-500">{path.path}</p>
                              {path.description && (
                                <p className="text-sm text-gray-600 mt-1">
                                  {path.description}
                                </p>
                              )}
                            </div>
                          </div>
                          <div className="text-right">
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${getEngineColor(
                                path.engine
                              )}`}
                            >
                              {path.engine}
                            </span>
                            <p className="text-xs text-gray-500 mt-2">
                              {path.access_count.toLocaleString()} accesses
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Integrations Tab */}
                {activeTab === 'integrations' && (
                  <div className="space-y-4">
                    {integrations.map((integration) => (
                      <div
                        key={integration.id}
                        className="border border-gray-200 rounded-lg p-4"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h4 className="font-medium text-gray-900">
                              Playbook: {integration.playbook_id}
                            </h4>
                            <p className="text-sm text-gray-500">
                              Inject as: {integration.inject_as}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            {integration.enabled ? (
                              <span className="flex items-center gap-1 text-xs text-green-600">
                                <CheckCircleIcon className="h-4 w-4" />
                                Enabled
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-xs text-gray-400">
                                <XCircleIcon className="h-4 w-4" />
                                Disabled
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="mb-3">
                          <p className="text-sm text-gray-500 mb-1">Secret Paths:</p>
                          <div className="flex flex-wrap gap-1">
                            {integration.secret_paths.map((path) => (
                              <span
                                key={path}
                                className="px-2 py-1 bg-gray-100 rounded text-xs font-mono"
                              >
                                {path}
                              </span>
                            ))}
                          </div>
                        </div>

                        {Object.keys(integration.environment_variables).length > 0 && (
                          <div>
                            <p className="text-sm text-gray-500 mb-1">
                              Environment Variables:
                            </p>
                            <div className="bg-gray-50 rounded p-2">
                              {Object.entries(integration.environment_variables).map(
                                ([key, value]) => (
                                  <div key={key} className="text-xs font-mono">
                                    <span className="text-blue-600">{key}</span>
                                    <span className="text-gray-400"> = </span>
                                    <span className="text-gray-600">{value}</span>
                                  </div>
                                )
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Policies Tab */}
                {activeTab === 'policies' && (
                  <div className="space-y-4">
                    {policies.map((policy) => (
                      <div
                        key={policy.name}
                        className="border border-gray-200 rounded-lg p-4"
                      >
                        <h4 className="font-medium text-gray-900 mb-3">{policy.name}</h4>
                        <div className="space-y-2">
                          {policy.rules.map((rule, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between bg-gray-50 rounded p-2"
                            >
                              <span className="text-sm font-mono text-gray-700">
                                {rule.path}
                              </span>
                              <div className="flex gap-1">
                                {rule.capabilities.map((cap) => (
                                  <span
                                    key={cap}
                                    className={`px-2 py-0.5 rounded text-xs font-medium ${
                                      cap === 'deny'
                                        ? 'bg-red-100 text-red-700'
                                        : cap === 'sudo'
                                        ? 'bg-purple-100 text-purple-700'
                                        : 'bg-blue-100 text-blue-700'
                                    }`}
                                  >
                                    {cap}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
