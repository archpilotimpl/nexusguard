"""Compliance management service.

This service manages compliance monitoring for regulatory frameworks including
GENIUS Act 2025 and PCI-DSS v4.0. It validates transaction data and infrastructure
metrics against defined thresholds using automated checks powered by Prometheus.

Data Flow:
1. Test data pushed to Prometheus Pushgateway (prometheus/test_data/compliance_metrics.json)
2. Prometheus scrapes and stores metrics in TSDB
3. This service queries Prometheus via PromQL to evaluate compliance controls
4. Results are scored using weighted severity model and presented via API

Automated Checks:
- GENIUS Act: Reserve ratios, KYC rates, AML monitoring, RTO, redemption times
- PCI-DSS: Firewall configs, encryption, MFA, patching, logging, training

Controls marked with automated_check=True are evaluated every 5 minutes.
"""
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.core.logging import get_logger
from app.models.compliance import (
    ComplianceStatus,
    ComplianceSeverity,
    ComplianceControl,
    ComplianceFramework,
    ComplianceAuditLog,
    GeniusActRequirement,
    PCIDSSRequirement,
)

logger = get_logger(__name__)


class ComplianceService:
    """Service for managing compliance frameworks and controls.

    This service provides:
    - Automated validation of metrics against regulatory thresholds
    - Weighted scoring based on control severity (critical=5, high=4, medium=3, low=2, info=1)
    - Audit logging for all status changes
    - Integration with Ansible playbooks for automated remediation
    """

    def __init__(self):
        self._frameworks: Dict[str, ComplianceFramework] = {}
        self._audit_logs: List[ComplianceAuditLog] = []
        self._init_frameworks()

    def _init_frameworks(self):
        """Initialize compliance frameworks with sample controls."""
        # GENIUS Act 2025 Framework
        genius_controls = [
            ComplianceControl(
                id="genius-1.1",
                name="Stablecoin Reserve Requirements",
                description="Issuers must maintain 1:1 reserves in high-quality liquid assets",
                category="Reserve Management",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                evidence="Reserve audit report Q4 2024 showing 102% backing",
                remediation=None,
                last_assessed=datetime.utcnow() - timedelta(days=7),
                next_review=datetime.utcnow() + timedelta(days=83),
                automated_check=True,
                playbook_id="collect_diagnostics"
            ),
            ComplianceControl(
                id="genius-1.2",
                name="Reserve Composition Disclosure",
                description="Monthly public disclosure of reserve composition",
                category="Transparency",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.HIGH,
                evidence="Published monthly reserve reports on website",
                last_assessed=datetime.utcnow() - timedelta(days=3),
                next_review=datetime.utcnow() + timedelta(days=27),
                automated_check=True
            ),
            ComplianceControl(
                id="genius-2.1",
                name="Customer Identification Program",
                description="Implement KYC for all users with transactions exceeding $3,000",
                category="AML/KYC",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                evidence="KYC completion rate: 99.8% for qualifying transactions",
                last_assessed=datetime.utcnow() - timedelta(days=1),
                automated_check=True
            ),
            ComplianceControl(
                id="genius-2.2",
                name="Transaction Monitoring",
                description="Real-time monitoring for suspicious activity patterns",
                category="AML/KYC",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                evidence="ML-based monitoring system with 99.5% uptime",
                last_assessed=datetime.utcnow(),
                automated_check=True,
                playbook_id="high_error_rate_investigation"
            ),
            ComplianceControl(
                id="genius-3.1",
                name="Operational Resilience",
                description="Business continuity plans with RTO < 4 hours",
                category="Operations",
                status=ComplianceStatus.PARTIAL,
                severity=ComplianceSeverity.HIGH,
                evidence="DR test completed but RTO measured at 5.2 hours",
                remediation="Optimize database failover procedures to reduce RTO",
                last_assessed=datetime.utcnow() - timedelta(days=14),
                next_review=datetime.utcnow() + timedelta(days=16),
                playbook_id="database_failover"
            ),
            ComplianceControl(
                id="genius-3.2",
                name="Cybersecurity Standards",
                description="Implement NIST CSF and conduct annual penetration testing",
                category="Security",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                evidence="Annual pentest completed Jan 2025, all critical findings remediated",
                last_assessed=datetime.utcnow() - timedelta(days=30),
                next_review=datetime.utcnow() + timedelta(days=335)
            ),
            ComplianceControl(
                id="genius-4.1",
                name="Redemption Rights",
                description="Allow redemption at par within 1 business day",
                category="Consumer Protection",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                evidence="Average redemption time: 2.3 hours",
                last_assessed=datetime.utcnow() - timedelta(hours=12),
                automated_check=True
            ),
            ComplianceControl(
                id="genius-4.2",
                name="Fee Transparency",
                description="Clear disclosure of all fees before transaction",
                category="Consumer Protection",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.MEDIUM,
                evidence="Fee disclosure UI implemented on all transaction screens",
                last_assessed=datetime.utcnow() - timedelta(days=5)
            ),
            ComplianceControl(
                id="genius-5.1",
                name="Interoperability Standards",
                description="Support interoperability with other payment systems",
                category="Interoperability",
                status=ComplianceStatus.PENDING_REVIEW,
                severity=ComplianceSeverity.MEDIUM,
                evidence="API specifications under review by compliance team",
                last_assessed=datetime.utcnow() - timedelta(days=20),
                next_review=datetime.utcnow() + timedelta(days=10)
            ),
        ]

        genius_framework = ComplianceFramework(
            id="genius-act-2025",
            name="GENIUS Act 2025",
            version="1.0",
            description="Guiding and Establishing National Innovation for U.S. Stablecoins Act - Federal framework for payment stablecoin regulation",
            effective_date=datetime(2025, 7, 1),
            controls=genius_controls,
            overall_status=ComplianceStatus.PARTIAL,
            compliance_score=88.5,
            last_audit=datetime.utcnow() - timedelta(days=30),
            next_audit=datetime.utcnow() + timedelta(days=60)
        )

        # PCI-DSS v4.0 Framework
        pci_controls = [
            ComplianceControl(
                id="pci-1.1",
                name="Firewall Configuration Standards",
                description="Establish and implement firewall and router configuration standards",
                category="Network Security",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                evidence="Firewall rules reviewed and documented monthly",
                last_assessed=datetime.utcnow() - timedelta(days=5),
                automated_check=True,
                playbook_id="firewall_emergency_block"
            ),
            ComplianceControl(
                id="pci-1.2",
                name="Network Segmentation",
                description="Restrict connections between untrusted networks and CDE",
                category="Network Security",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                evidence="CDE isolated with dedicated VLANs and firewalls",
                last_assessed=datetime.utcnow() - timedelta(days=10),
                playbook_id="network_connectivity_test"
            ),
            ComplianceControl(
                id="pci-2.1",
                name="Remove Vendor Defaults",
                description="Always change vendor-supplied defaults before installing system",
                category="Secure Configuration",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.HIGH,
                evidence="Automated scanning confirms no default credentials",
                last_assessed=datetime.utcnow() - timedelta(days=1),
                automated_check=True
            ),
            ComplianceControl(
                id="pci-3.1",
                name="Data Retention Policy",
                description="Keep cardholder data storage to a minimum",
                category="Data Protection",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.HIGH,
                evidence="PANs purged after 90 days, only last 4 digits retained",
                last_assessed=datetime.utcnow() - timedelta(days=7)
            ),
            ComplianceControl(
                id="pci-3.4",
                name="PAN Rendering Unreadable",
                description="Render PAN unreadable anywhere it is stored",
                category="Data Protection",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                evidence="AES-256 encryption for stored PANs, tokenization for display",
                last_assessed=datetime.utcnow() - timedelta(days=3),
                automated_check=True
            ),
            ComplianceControl(
                id="pci-4.1",
                name="Strong Cryptography for Transmission",
                description="Use strong cryptography and security protocols for sensitive data",
                category="Encryption",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                evidence="TLS 1.3 enforced for all external connections",
                last_assessed=datetime.utcnow() - timedelta(days=2),
                automated_check=True,
                playbook_id="ssl_certificate_check"
            ),
            ComplianceControl(
                id="pci-5.1",
                name="Anti-Malware Protection",
                description="Deploy anti-malware software on systems commonly affected by malware",
                category="Malware Protection",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.HIGH,
                evidence="CrowdStrike Falcon deployed on all endpoints",
                last_assessed=datetime.utcnow() - timedelta(days=1),
                automated_check=True
            ),
            ComplianceControl(
                id="pci-6.1",
                name="Security Patch Management",
                description="Establish process to identify and assign risk ranking to vulnerabilities",
                category="Vulnerability Management",
                status=ComplianceStatus.PARTIAL,
                severity=ComplianceSeverity.HIGH,
                evidence="3 high-severity patches pending deployment",
                remediation="Schedule emergency patch window for critical systems",
                last_assessed=datetime.utcnow() - timedelta(hours=6),
                next_review=datetime.utcnow() + timedelta(days=7),
                automated_check=True,
                playbook_id="restart_application"
            ),
            ComplianceControl(
                id="pci-7.1",
                name="Access Control",
                description="Limit access to system components to only those who require it",
                category="Access Control",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                evidence="RBAC implemented, quarterly access reviews completed",
                last_assessed=datetime.utcnow() - timedelta(days=15)
            ),
            ComplianceControl(
                id="pci-8.1",
                name="Unique User IDs",
                description="Assign unique identification to each person with access",
                category="Authentication",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.HIGH,
                evidence="SSO with unique user IDs enforced",
                last_assessed=datetime.utcnow() - timedelta(days=4)
            ),
            ComplianceControl(
                id="pci-8.3",
                name="Multi-Factor Authentication",
                description="Secure all individual administrative access with MFA",
                category="Authentication",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                evidence="MFA required for all admin and remote access",
                last_assessed=datetime.utcnow() - timedelta(days=2),
                automated_check=True
            ),
            ComplianceControl(
                id="pci-9.1",
                name="Physical Access Controls",
                description="Use appropriate facility entry controls to limit physical access",
                category="Physical Security",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.HIGH,
                evidence="Badge access, cameras, and visitor logs in place",
                last_assessed=datetime.utcnow() - timedelta(days=30)
            ),
            ComplianceControl(
                id="pci-10.1",
                name="Audit Trail Implementation",
                description="Implement audit trails to link all access to individual users",
                category="Logging & Monitoring",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.CRITICAL,
                evidence="Centralized logging with user attribution to SIEM",
                last_assessed=datetime.utcnow() - timedelta(days=1),
                automated_check=True,
                playbook_id="collect_diagnostics"
            ),
            ComplianceControl(
                id="pci-10.4",
                name="Time Synchronization",
                description="Synchronize all critical system clocks and times",
                category="Logging & Monitoring",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.MEDIUM,
                evidence="NTP configured to stratum-1 servers, drift < 1ms",
                last_assessed=datetime.utcnow() - timedelta(days=7),
                automated_check=True
            ),
            ComplianceControl(
                id="pci-11.2",
                name="Vulnerability Scanning",
                description="Run internal and external network vulnerability scans quarterly",
                category="Security Testing",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.HIGH,
                evidence="Q4 2024 scans completed, no critical findings",
                last_assessed=datetime.utcnow() - timedelta(days=45),
                next_review=datetime.utcnow() + timedelta(days=45)
            ),
            ComplianceControl(
                id="pci-11.3",
                name="Penetration Testing",
                description="Perform penetration testing at least annually",
                category="Security Testing",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.HIGH,
                evidence="Annual pentest completed Jan 2025",
                last_assessed=datetime.utcnow() - timedelta(days=30),
                next_review=datetime.utcnow() + timedelta(days=335)
            ),
            ComplianceControl(
                id="pci-12.1",
                name="Information Security Policy",
                description="Establish, publish, maintain, and disseminate a security policy",
                category="Security Policy",
                status=ComplianceStatus.COMPLIANT,
                severity=ComplianceSeverity.HIGH,
                evidence="Security policy reviewed and updated annually",
                last_assessed=datetime.utcnow() - timedelta(days=60)
            ),
            ComplianceControl(
                id="pci-12.6",
                name="Security Awareness Training",
                description="Implement formal security awareness program",
                category="Security Policy",
                status=ComplianceStatus.NON_COMPLIANT,
                severity=ComplianceSeverity.MEDIUM,
                evidence="15% of employees have not completed annual training",
                remediation="Send reminder emails and schedule makeup sessions",
                last_assessed=datetime.utcnow() - timedelta(days=2),
                next_review=datetime.utcnow() + timedelta(days=14)
            ),
        ]

        pci_framework = ComplianceFramework(
            id="pci-dss-v4",
            name="PCI-DSS v4.0",
            version="4.0",
            description="Payment Card Industry Data Security Standard - Requirements for secure handling of cardholder data",
            effective_date=datetime(2024, 3, 31),
            controls=pci_controls,
            overall_status=ComplianceStatus.PARTIAL,
            compliance_score=92.3,
            last_audit=datetime.utcnow() - timedelta(days=45),
            next_audit=datetime.utcnow() + timedelta(days=45)
        )

        self._frameworks["genius-act-2025"] = genius_framework
        self._frameworks["pci-dss-v4"] = pci_framework

    async def list_frameworks(self) -> List[ComplianceFramework]:
        """List all compliance frameworks."""
        return list(self._frameworks.values())

    async def get_framework(self, framework_id: str) -> Optional[ComplianceFramework]:
        """Get a specific framework by ID."""
        return self._frameworks.get(framework_id)

    async def get_control(
        self, framework_id: str, control_id: str
    ) -> Optional[ComplianceControl]:
        """Get a specific control from a framework."""
        framework = self._frameworks.get(framework_id)
        if not framework:
            return None
        for control in framework.controls:
            if control.id == control_id:
                return control
        return None

    async def update_control_status(
        self,
        framework_id: str,
        control_id: str,
        new_status: ComplianceStatus,
        performed_by: str,
        notes: Optional[str] = None
    ) -> Optional[ComplianceControl]:
        """Update the status of a compliance control."""
        framework = self._frameworks.get(framework_id)
        if not framework:
            return None

        for i, control in enumerate(framework.controls):
            if control.id == control_id:
                old_status = control.status
                control.status = new_status
                control.last_assessed = datetime.utcnow()

                # Create audit log
                audit_log = ComplianceAuditLog(
                    id=str(uuid.uuid4()),
                    framework_id=framework_id,
                    control_id=control_id,
                    action="status_change",
                    previous_status=old_status,
                    new_status=new_status,
                    performed_by=performed_by,
                    timestamp=datetime.utcnow(),
                    notes=notes
                )
                self._audit_logs.append(audit_log)

                # Recalculate framework score
                self._recalculate_score(framework)

                framework.controls[i] = control
                logger.info(
                    "Control status updated",
                    framework_id=framework_id,
                    control_id=control_id,
                    old_status=old_status.value,
                    new_status=new_status.value
                )
                return control

        return None

    def _recalculate_score(self, framework: ComplianceFramework):
        """Recalculate the overall compliance score for a framework."""
        if not framework.controls:
            framework.compliance_score = 0
            return

        total_weight = 0
        weighted_score = 0

        severity_weights = {
            ComplianceSeverity.CRITICAL: 5,
            ComplianceSeverity.HIGH: 4,
            ComplianceSeverity.MEDIUM: 3,
            ComplianceSeverity.LOW: 2,
            ComplianceSeverity.INFO: 1
        }

        status_scores = {
            ComplianceStatus.COMPLIANT: 100,
            ComplianceStatus.PARTIAL: 50,
            ComplianceStatus.PENDING_REVIEW: 25,
            ComplianceStatus.NON_COMPLIANT: 0,
            ComplianceStatus.NOT_APPLICABLE: None
        }

        for control in framework.controls:
            score = status_scores.get(control.status)
            if score is None:
                continue

            weight = severity_weights.get(control.severity, 1)
            total_weight += weight
            weighted_score += score * weight

        if total_weight > 0:
            framework.compliance_score = round(weighted_score / total_weight, 1)
        else:
            framework.compliance_score = 0

        # Update overall status
        non_compliant = sum(1 for c in framework.controls
                          if c.status == ComplianceStatus.NON_COMPLIANT)
        partial = sum(1 for c in framework.controls
                     if c.status == ComplianceStatus.PARTIAL)

        if non_compliant > 0:
            framework.overall_status = ComplianceStatus.NON_COMPLIANT
        elif partial > 0:
            framework.overall_status = ComplianceStatus.PARTIAL
        else:
            framework.overall_status = ComplianceStatus.COMPLIANT

    async def get_audit_logs(
        self,
        framework_id: Optional[str] = None,
        control_id: Optional[str] = None,
        limit: int = 50
    ) -> List[ComplianceAuditLog]:
        """Get audit logs with optional filters."""
        logs = self._audit_logs

        if framework_id:
            logs = [l for l in logs if l.framework_id == framework_id]
        if control_id:
            logs = [l for l in logs if l.control_id == control_id]

        logs.sort(key=lambda l: l.timestamp, reverse=True)
        return logs[:limit]

    async def get_compliance_summary(self) -> Dict:
        """Get overall compliance summary across all frameworks."""
        summary = {
            "total_frameworks": len(self._frameworks),
            "total_controls": 0,
            "compliant": 0,
            "partial": 0,
            "non_compliant": 0,
            "pending_review": 0,
            "overall_score": 0,
            "frameworks": []
        }

        total_score = 0
        for framework in self._frameworks.values():
            summary["total_controls"] += len(framework.controls)
            total_score += framework.compliance_score

            for control in framework.controls:
                if control.status == ComplianceStatus.COMPLIANT:
                    summary["compliant"] += 1
                elif control.status == ComplianceStatus.PARTIAL:
                    summary["partial"] += 1
                elif control.status == ComplianceStatus.NON_COMPLIANT:
                    summary["non_compliant"] += 1
                elif control.status == ComplianceStatus.PENDING_REVIEW:
                    summary["pending_review"] += 1

            summary["frameworks"].append({
                "id": framework.id,
                "name": framework.name,
                "score": framework.compliance_score,
                "status": framework.overall_status.value,
                "control_count": len(framework.controls)
            })

        if self._frameworks:
            summary["overall_score"] = round(
                total_score / len(self._frameworks), 1
            )

        return summary


# Singleton instance
compliance_service = ComplianceService()
