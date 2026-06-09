from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.models import HealthSnapshot, OperationalSnapshot
from app.services.digest import DataDigest
from app.services.graph.coverage import GraphCoverage
from app.services.rules.types import RuleFinding, RuleScope


@dataclass
class AnalysisContext:
    """Runtime orchestration object during report generation — not persisted."""

    org_id: UUID
    period: str
    source_job_ids: list[UUID] | None
    domains: set[str]
    digest: DataDigest | None = None
    op_snap: OperationalSnapshot | None = None
    prior_op_snap: OperationalSnapshot | None = None
    prior_health: HealthSnapshot | None = None
    coverage: GraphCoverage | None = None
    findings: list[RuleFinding] = field(default_factory=list)

    @property
    def scope(self) -> RuleScope:
        return RuleScope(
            period=self.period,
            source_job_ids=self.source_job_ids,
            domains=self.domains or None,
        )

    def includes(self, domain: str) -> bool:
        return self.scope.includes(domain)
