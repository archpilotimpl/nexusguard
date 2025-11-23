"""Compliance and regulation models."""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    PENDING_REVIEW = "pending_review"
    NOT_APPLICABLE = "not_applicable"


class ComplianceSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceControl(BaseModel):
    """Individual compliance control/requirement."""
    id: str
    name: str
    description: str
    category: str
    status: ComplianceStatus
    severity: ComplianceSeverity
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    last_assessed: datetime
    next_review: Optional[datetime] = None
    automated_check: bool = False
    playbook_id: Optional[str] = None


class ComplianceFramework(BaseModel):
    """Compliance framework (e.g., PCI-DSS, GENIUS Act)."""
    id: str
    name: str
    version: str
    description: str
    effective_date: datetime
    controls: List[ComplianceControl]
    overall_status: ComplianceStatus
    compliance_score: float = Field(ge=0, le=100)
    last_audit: Optional[datetime] = None
    next_audit: Optional[datetime] = None


class ComplianceAuditLog(BaseModel):
    """Audit log entry for compliance changes."""
    id: str
    framework_id: str
    control_id: str
    action: str
    previous_status: Optional[ComplianceStatus] = None
    new_status: ComplianceStatus
    performed_by: str
    timestamp: datetime
    notes: Optional[str] = None


class GeniusActRequirement(BaseModel):
    """GENIUS Act 2025 specific requirement."""
    section: str
    requirement: str
    applies_to: List[str]
    implementation_deadline: datetime
    penalty_info: Optional[str] = None


class PCIDSSRequirement(BaseModel):
    """PCI-DSS specific requirement."""
    requirement_id: str
    requirement_name: str
    testing_procedures: List[str]
    guidance: str
    applies_to_level: List[int]  # PCI levels 1-4
