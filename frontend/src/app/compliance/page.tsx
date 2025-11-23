'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { complianceApi } from '@/lib/api';
import type { ComplianceFramework, ComplianceSummary } from '@/types';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ClockIcon,
  ShieldCheckIcon,
  DocumentCheckIcon,
} from '@heroicons/react/24/outline';

export default function CompliancePage() {
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [frameworks, setFrameworks] = useState<ComplianceFramework[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFramework, setSelectedFramework] = useState<string | null>(null);
  const [expandedControl, setExpandedControl] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [summaryData, frameworksData] = await Promise.all([
          complianceApi.getSummary(),
          complianceApi.listFrameworks(),
        ]);
        setSummary(summaryData);
        setFrameworks(frameworksData);
        if (frameworksData.length > 0) {
          setSelectedFramework(frameworksData[0].id);
        }
      } catch (error) {
        console.error('Failed to fetch compliance data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'partial':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'non_compliant':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'pending_review':
        return <ClockIcon className="h-5 w-5 text-blue-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      compliant: 'bg-green-100 text-green-800',
      partial: 'bg-yellow-100 text-yellow-800',
      non_compliant: 'bg-red-100 text-red-800',
      pending_review: 'bg-blue-100 text-blue-800',
      not_applicable: 'bg-gray-100 text-gray-800',
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  const getSeverityBadge = (severity: string) => {
    const styles: Record<string, string> = {
      critical: 'bg-red-100 text-red-800',
      high: 'bg-orange-100 text-orange-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-blue-100 text-blue-800',
      info: 'bg-gray-100 text-gray-800',
    };
    return styles[severity] || 'bg-gray-100 text-gray-800';
  };

  const selectedFrameworkData = frameworks.find((f) => f.id === selectedFramework);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Compliance & Regulations</h1>
            <p className="text-sm text-gray-500 mt-1">
              Monitor compliance status for GENIUS Act 2025 and PCI-DSS v4.0
            </p>
          </div>
        </div>

        {/* Descriptive Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <ShieldCheckIcon className="h-8 w-8 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                Automated Compliance Validation
              </h3>
              <p className="text-sm text-blue-800 mb-3">
                This compliance monitoring system continuously validates transaction data and infrastructure metrics
                against regulatory thresholds defined by GENIUS Act 2025 and PCI-DSS v4.0 standards. All checks are
                automated using Prometheus test data from <code className="bg-blue-100 px-1 py-0.5 rounded text-xs">prometheus/test_data/compliance_metrics.json</code>.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-blue-700">
                <div className="flex items-start gap-2">
                  <CheckCircleIcon className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <strong>GENIUS Act 2025:</strong> Validates stablecoin reserve ratios, KYC completion rates,
                    transaction monitoring uptime, disaster recovery RTO, and redemption processing times against
                    regulatory thresholds.
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircleIcon className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <strong>PCI-DSS v4.0:</strong> Monitors firewall configurations, credential security,
                    encryption standards, TLS versions, anti-malware coverage, patch compliance, MFA enforcement,
                    audit logging, time synchronization, and security training completion.
                  </div>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-blue-200">
                <p className="text-xs text-blue-700">
                  <strong>Data Source:</strong> Metrics are collected from Prometheus via Pushgateway,
                  evaluated against predefined thresholds, and scored using a weighted severity model.
                  Controls marked as "Auto" are automatically checked every 5 minutes.
                </p>
              </div>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent"></div>
          </div>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary-100 rounded-lg">
                    <ShieldCheckIcon className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Overall Score</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {summary?.overall_score.toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <CheckCircleIcon className="h-6 w-6 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Compliant</p>
                    <p className="text-2xl font-bold text-gray-900">{summary?.compliant}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Partial / Review</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {(summary?.partial || 0) + (summary?.pending_review || 0)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <XCircleIcon className="h-6 w-6 text-red-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Non-Compliant</p>
                    <p className="text-2xl font-bold text-gray-900">{summary?.non_compliant}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Framework Tabs */}
            <div className="bg-white rounded-lg shadow">
              <div className="border-b border-gray-200">
                <nav className="flex -mb-px">
                  {frameworks.map((framework) => (
                    <button
                      key={framework.id}
                      onClick={() => setSelectedFramework(framework.id)}
                      className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                        selectedFramework === framework.id
                          ? 'border-primary-500 text-primary-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <DocumentCheckIcon className="h-5 w-5" />
                        {framework.name}
                        <span
                          className={`ml-2 px-2 py-0.5 rounded-full text-xs ${getStatusBadge(
                            framework.overall_status
                          )}`}
                        >
                          {framework.compliance_score.toFixed(1)}%
                        </span>
                      </div>
                    </button>
                  ))}
                </nav>
              </div>

              {selectedFrameworkData && (
                <div className="p-6">
                  {/* Framework Info */}
                  <div className="mb-6">
                    <h2 className="text-lg font-semibold text-gray-900">
                      {selectedFrameworkData.name} v{selectedFrameworkData.version}
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">
                      {selectedFrameworkData.description}
                    </p>
                    <div className="flex gap-4 mt-3 text-sm text-gray-500">
                      <span>
                        Effective: {formatDate(selectedFrameworkData.effective_date)}
                      </span>
                      {selectedFrameworkData.next_audit && (
                        <span>
                          Next Audit: {formatDate(selectedFrameworkData.next_audit)}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Key Requirements Summary */}
                  <div className="mb-6 bg-gray-50 rounded-lg p-5 border border-gray-200">
                    <h3 className="text-sm font-semibold text-gray-900 mb-3">
                      Key Requirements Overview
                    </h3>
                    {selectedFrameworkData.id === 'genius-act-2025' ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            1
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Reserve Requirements:</strong>
                            <span className="text-gray-600"> Maintain 1:1 backing ratio with high-quality liquid assets (Treasury bills, bank deposits, reverse repos)</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            2
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Transparency & Disclosure:</strong>
                            <span className="text-gray-600"> Publish monthly reports detailing reserve composition and audit attestations</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            3
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">KYC/AML Compliance:</strong>
                            <span className="text-gray-600"> Implement Know Your Customer for transactions exceeding $3,000 and real-time AML monitoring</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            4
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Operational Resilience:</strong>
                            <span className="text-gray-600"> Business continuity plans with RTO {'<'} 4 hours and annual disaster recovery testing</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            5
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Cybersecurity Standards:</strong>
                            <span className="text-gray-600"> Implement NIST Cybersecurity Framework and conduct annual penetration testing</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            6
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Consumer Protection:</strong>
                            <span className="text-gray-600"> Enable redemption at par within 1 business day with clear fee disclosure</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            7
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Interoperability:</strong>
                            <span className="text-gray-600"> Support seamless integration with other payment systems and digital wallets</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            8
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Regulatory Reporting:</strong>
                            <span className="text-gray-600"> Submit quarterly compliance reports to federal regulators with transaction volume metrics</span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            1
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Build & Maintain Secure Network:</strong>
                            <span className="text-gray-600"> Install and maintain firewall configurations, eliminate vendor defaults, restrict cardholder data access</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            2
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Protect Cardholder Data:</strong>
                            <span className="text-gray-600"> Encrypt transmission over open networks, render PAN unreadable with AES-256, minimize data retention</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            3
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Vulnerability Management:</strong>
                            <span className="text-gray-600"> Deploy anti-malware on all systems, patch critical vulnerabilities within 30 days, secure development practices</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            4
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Strong Access Controls:</strong>
                            <span className="text-gray-600"> Limit data access on need-to-know basis, assign unique IDs, enforce MFA for all admin access</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            5
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Monitor & Test Networks:</strong>
                            <span className="text-gray-600"> Track all access with audit trails, quarterly vulnerability scans, annual penetration testing</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            6
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Information Security Policy:</strong>
                            <span className="text-gray-600"> Maintain security policy addressing all requirements, annual security awareness training for all personnel</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            7
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Cryptographic Controls:</strong>
                            <span className="text-gray-600"> Use TLS 1.2+ for all transmissions, strong cryptography for key management, secure key storage in HSM/Vault</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            8
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Physical Security:</strong>
                            <span className="text-gray-600"> Facility access controls with badge systems, video surveillance, visitor logs, and secure media disposal</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            9
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Incident Response:</strong>
                            <span className="text-gray-600"> Documented incident response plan, 24/7 security monitoring, forensic analysis capabilities</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2">
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-bold mt-0.5">
                            10
                          </div>
                          <div className="text-sm">
                            <strong className="text-gray-800">Third-Party Management:</strong>
                            <span className="text-gray-600"> Maintain list of service providers, ensure PCI-DSS compliance for all vendors handling cardholder data</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Controls List */}
                  <div className="space-y-3">
                    {selectedFrameworkData.controls.map((control) => (
                      <div
                        key={control.id}
                        className="border border-gray-200 rounded-lg overflow-hidden"
                      >
                        <div
                          className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
                          onClick={() =>
                            setExpandedControl(
                              expandedControl === control.id ? null : control.id
                            )
                          }
                        >
                          <div className="flex items-center gap-3">
                            {getStatusIcon(control.status)}
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-gray-700">
                                  {control.id}
                                </span>
                                <span className="font-medium text-gray-900">
                                  {control.name}
                                </span>
                              </div>
                              <p className="text-sm text-gray-500">{control.category}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${getSeverityBadge(
                                control.severity
                              )}`}
                            >
                              {control.severity}
                            </span>
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${getStatusBadge(
                                control.status
                              )}`}
                            >
                              {control.status.replace('_', ' ')}
                            </span>
                            {control.automated_check && (
                              <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                Auto
                              </span>
                            )}
                          </div>
                        </div>

                        {expandedControl === control.id && (
                          <div className="border-t border-gray-200 bg-gray-50 p-4">
                            <div className="space-y-3">
                              <div>
                                <h4 className="text-sm font-medium text-gray-700">
                                  Description
                                </h4>
                                <p className="text-sm text-gray-600">{control.description}</p>
                              </div>

                              {control.evidence && (
                                <div>
                                  <h4 className="text-sm font-medium text-gray-700">
                                    Evidence
                                  </h4>
                                  <p className="text-sm text-gray-600">{control.evidence}</p>
                                </div>
                              )}

                              {control.remediation && (
                                <div>
                                  <h4 className="text-sm font-medium text-gray-700">
                                    Remediation Required
                                  </h4>
                                  <p className="text-sm text-red-600">{control.remediation}</p>
                                </div>
                              )}

                              <div className="flex gap-6 text-sm">
                                <div>
                                  <span className="text-gray-500">Last Assessed: </span>
                                  <span className="text-gray-700">
                                    {formatDate(control.last_assessed)}
                                  </span>
                                </div>
                                {control.next_review && (
                                  <div>
                                    <span className="text-gray-500">Next Review: </span>
                                    <span className="text-gray-700">
                                      {formatDate(control.next_review)}
                                    </span>
                                  </div>
                                )}
                                {control.playbook_id && (
                                  <div>
                                    <span className="text-gray-500">Playbook: </span>
                                    <span className="text-primary-600">
                                      {control.playbook_id}
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
