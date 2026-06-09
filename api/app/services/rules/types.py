from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class RuleScope:
    period: str | None = None
    source_job_ids: list[UUID] | None = None
    domains: set[str] | None = None

    def includes(self, domain: str) -> bool:
        return self.domains is None or domain in self.domains


@dataclass
class RuleFinding:
    finding_type: str
    title: str
    detail: str
    severity: str
    confidence: float
    business_impact: str
    department: str
    category: str
    suggested_action: str
    finding_id: str = ""
    finding_instance_id: str = ""
    source_metric_keys: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        raw = f"{self.finding_type}:{self.title}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def to_dict(self) -> dict:
        return {
            "finding_type": self.finding_type,
            "title": self.title,
            "detail": self.detail,
            "severity": self.severity,
            "confidence": self.confidence,
            "business_impact": self.business_impact,
            "department": self.department,
            "category": self.category,
            "suggested_action": self.suggested_action,
            "fingerprint": self.fingerprint,
            "finding_id": self.finding_id,
            "finding_instance_id": self.finding_instance_id,
            "source_metric_keys": self.source_metric_keys,
            "evidence": self.evidence,
        }
