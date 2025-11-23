'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { ansibleApi } from '@/lib/api';
import type { Playbook } from '@/types';
import toast from 'react-hot-toast';

export default function PlaybooksPage() {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [expandedPlaybook, setExpandedPlaybook] = useState<string | null>(null);

  useEffect(() => {
    const fetchPlaybooks = async () => {
      try {
        const data = await ansibleApi.listPlaybooks(selectedCategory || undefined);
        setPlaybooks(data);
      } catch (error) {
        console.error('Failed to fetch playbooks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPlaybooks();
  }, [selectedCategory]);

  const handleRunPlaybook = async (playbookId: string) => {
    try {
      await ansibleApi.runPlaybook({ playbook_id: playbookId, dry_run: true });
      toast.success('Playbook dry-run started');
    } catch (error) {
      toast.error('Failed to run playbook');
    }
  };

  const toggleExpand = (playbookId: string) => {
    setExpandedPlaybook(expandedPlaybook === playbookId ? null : playbookId);
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Ansible Playbooks</h1>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">All Categories</option>
            <option value="application">Application</option>
            <option value="network">Network</option>
            <option value="infrastructure">Infrastructure</option>
            <option value="database">Database</option>
            <option value="security">Security</option>
          </select>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent"></div>
          </div>
        ) : playbooks.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500">No playbooks found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {playbooks.map((playbook) => (
              <div key={playbook.id} className="bg-white rounded-lg shadow">
                <div className="p-6">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-medium text-gray-900">{playbook.name}</h3>
                    <span className="text-xs px-2 py-1 bg-gray-100 rounded-full">
                      {playbook.category}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-4">{playbook.description}</p>

                  {/* Incident Types */}
                  {playbook.incident_types.length > 0 && (
                    <div className="mb-4">
                      <div className="flex flex-wrap gap-1">
                        {playbook.incident_types.map((type) => (
                          <span
                            key={type}
                            className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded"
                          >
                            {type.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <div className="flex gap-2">
                      {playbook.requires_approval && (
                        <span className="text-xs text-yellow-600">Needs Approval</span>
                      )}
                      {playbook.is_automated && (
                        <span className="text-xs text-green-600">Automated</span>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => toggleExpand(playbook.id)}
                        className="px-3 py-1 border border-gray-300 text-gray-700 rounded text-sm font-medium hover:bg-gray-50"
                      >
                        {expandedPlaybook === playbook.id ? 'Hide Steps' : 'View Steps'}
                      </button>
                      <button
                        onClick={() => handleRunPlaybook(playbook.id)}
                        className="px-3 py-1 bg-primary-100 text-primary-700 rounded text-sm font-medium hover:bg-primary-200"
                      >
                        Dry Run
                      </button>
                    </div>
                  </div>
                </div>

                {/* Execution Steps */}
                {expandedPlaybook === playbook.id && playbook.steps && playbook.steps.length > 0 && (
                  <div className="border-t border-gray-100 bg-gray-50 p-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Execution Steps:</h4>
                    <div className="space-y-2">
                      {playbook.steps.map((step) => (
                        <div
                          key={step.order}
                          className="flex items-start gap-3 text-sm"
                        >
                          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-medium">
                            {step.order}
                          </span>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-gray-900">{step.name}</span>
                              {step.is_destructive && (
                                <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-600 rounded">
                                  Destructive
                                </span>
                              )}
                            </div>
                            <p className="text-gray-600">{step.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
