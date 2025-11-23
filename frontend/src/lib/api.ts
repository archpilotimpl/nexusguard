import axios from 'axios';
import type {
  MetricsSummary,
  Incident,
  Playbook,
  PlaybookExecution,
  SystemHealth,
  AuthTokens,
  ComplianceFramework,
  ComplianceControl,
  ComplianceSummary,
  ComplianceAuditLog,
  VaultHealth,
  VaultSummary,
  VaultSecretPath,
  AnsibleVaultIntegration,
  VaultPolicy
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8090/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  login: async (email: string, password: string): Promise<AuthTokens> => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },
  refresh: async (refreshToken: string): Promise<AuthTokens> => {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },
};

// Metrics
export const metricsApi = {
  getSummary: async (): Promise<MetricsSummary> => {
    const response = await api.get('/metrics/summary');
    return response.data;
  },
  getAlerts: async () => {
    const response = await api.get('/metrics/alerts');
    return response.data;
  },
};

// Incidents
export const incidentsApi = {
  list: async (params?: {
    status?: string;
    severity?: string;
    region?: string;
    limit?: number;
  }): Promise<Incident[]> => {
    const response = await api.get('/incidents', { params });
    return response.data;
  },
  get: async (id: string): Promise<Incident> => {
    const response = await api.get(`/incidents/${id}`);
    return response.data;
  },
  create: async (data: Partial<Incident>): Promise<Incident> => {
    const response = await api.post('/incidents', data);
    return response.data;
  },
  update: async (id: string, data: Partial<Incident>): Promise<Incident> => {
    const response = await api.patch(`/incidents/${id}`, data);
    return response.data;
  },
  acknowledge: async (id: string): Promise<Incident> => {
    const response = await api.post(`/incidents/${id}/acknowledge`);
    return response.data;
  },
  resolve: async (id: string, notes?: string): Promise<Incident> => {
    const response = await api.post(`/incidents/${id}/resolve`, null, {
      params: { resolution_notes: notes },
    });
    return response.data;
  },
  getStats: async () => {
    const response = await api.get('/incidents/stats');
    return response.data;
  },
};

// Ansible
export const ansibleApi = {
  listPlaybooks: async (category?: string): Promise<Playbook[]> => {
    const response = await api.get('/ansible/playbooks', { params: { category } });
    return response.data;
  },
  getPlaybook: async (id: string): Promise<Playbook> => {
    const response = await api.get(`/ansible/playbooks/${id}`);
    return response.data;
  },
  runPlaybook: async (request: {
    playbook_id: string;
    incident_id?: string;
    parameters?: Record<string, unknown>;
    target_hosts?: string[];
    dry_run?: boolean;
  }): Promise<PlaybookExecution> => {
    const response = await api.post('/ansible/run-playbook', request);
    return response.data;
  },
  listExecutions: async (params?: {
    playbook_id?: string;
    incident_id?: string;
    limit?: number;
  }): Promise<PlaybookExecution[]> => {
    const response = await api.get('/ansible/executions', { params });
    return response.data;
  },
  getExecution: async (id: string): Promise<PlaybookExecution> => {
    const response = await api.get(`/ansible/executions/${id}`);
    return response.data;
  },
};

// Health
export const healthApi = {
  check: async (): Promise<{ status: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
  detailed: async (): Promise<SystemHealth> => {
    const response = await api.get('/health/detailed');
    return response.data;
  },
};

// Compliance
export const complianceApi = {
  getSummary: async (): Promise<ComplianceSummary> => {
    const response = await api.get('/compliance/summary');
    return response.data;
  },
  listFrameworks: async (): Promise<ComplianceFramework[]> => {
    const response = await api.get('/compliance/frameworks');
    return response.data;
  },
  getFramework: async (id: string): Promise<ComplianceFramework> => {
    const response = await api.get(`/compliance/frameworks/${id}`);
    return response.data;
  },
  getControl: async (frameworkId: string, controlId: string): Promise<ComplianceControl> => {
    const response = await api.get(`/compliance/frameworks/${frameworkId}/controls/${controlId}`);
    return response.data;
  },
  updateControlStatus: async (
    frameworkId: string,
    controlId: string,
    status: string,
    notes?: string
  ): Promise<ComplianceControl> => {
    const response = await api.patch(
      `/compliance/frameworks/${frameworkId}/controls/${controlId}`,
      { status, notes }
    );
    return response.data;
  },
  getAuditLogs: async (params?: {
    framework_id?: string;
    control_id?: string;
    limit?: number;
  }): Promise<ComplianceAuditLog[]> => {
    const response = await api.get('/compliance/audit-logs', { params });
    return response.data;
  },
};

// Vault
export const vaultApi = {
  getHealth: async (): Promise<VaultHealth> => {
    const response = await api.get('/vault/health');
    return response.data;
  },
  getSummary: async (): Promise<VaultSummary> => {
    const response = await api.get('/vault/summary');
    return response.data;
  },
  listSecretPaths: async (): Promise<VaultSecretPath[]> => {
    const response = await api.get('/vault/secret-paths');
    return response.data;
  },
  listAnsibleIntegrations: async (): Promise<AnsibleVaultIntegration[]> => {
    const response = await api.get('/vault/ansible-integrations');
    return response.data;
  },
  getIntegrationForPlaybook: async (playbookId: string) => {
    const response = await api.get(`/vault/ansible-integrations/playbook/${playbookId}`);
    return response.data;
  },
  listPolicies: async (): Promise<VaultPolicy[]> => {
    const response = await api.get('/vault/policies');
    return response.data;
  },
  testConnection: async () => {
    const response = await api.post('/vault/test-connection');
    return response.data;
  },
};

export default api;
