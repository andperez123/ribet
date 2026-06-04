from __future__ import annotations

"""Hydrate report insight fields for legacy reports and API serialization."""

from sqlalchemy.orm import Session

from app.models import OperationalFinding, OperationalReport
from app.schemas.insights import (
    AnalysisMetadataOut,
    DataCoverageOut,
    DataDigestOut,
    DomainInsightOut,
)
from app.services.digest import (
    DataDigest,
    build_data_coverage,
    build_data_digest,
    build_domain_insights,
    digest_has_data,
)
from app.services.rules.runner import RuleFinding


def digest_from_dict(data: dict | None) -> DataDigest | None:
    if not data:
        return None
    digest = DataDigest()
    for key, val in data.items():
        if key in ("top_customers", "top_vendors"):
            continue
        if hasattr(digest, key):
            setattr(digest, key, val)
    from app.services.digest import TopEntry

    for tc in data.get("top_customers") or []:
        digest.top_customers.append(
            TopEntry(
                label=tc.get("label", ""),
                amount=float(tc.get("amount", 0)),
                pct=float(tc.get("pct", 0)),
                detail=tc.get("detail", ""),
            )
        )
    for tv in data.get("top_vendors") or []:
        digest.top_vendors.append(
            TopEntry(
                label=tv.get("label", ""),
                amount=float(tv.get("amount", 0)),
                pct=float(tv.get("pct", 0)),
                detail=tv.get("detail", ""),
            )
        )
    return digest


def _findings_from_report(report: OperationalReport) -> list[RuleFinding]:
    """Reconstruct RuleFinding-like objects from embedded report JSON."""
    findings: list[RuleFinding] = []
    for block in (
        (report.financial_findings or [])
        + (report.operational_findings or [])
        + (report.risk_areas or [])
    ):
        if not isinstance(block, dict) or not block.get("title"):
            continue
        findings.append(
            RuleFinding(
                finding_type=block.get("finding_type", "unknown"),
                title=block["title"],
                detail=block.get("detail", ""),
                severity=block.get("severity", "medium"),
                confidence=float(block.get("confidence", 0.8)),
                business_impact=block.get("business_impact", ""),
                department=block.get("department", ""),
                category=block.get("category", "operational"),
                suggested_action=block.get("suggested_action", ""),
            )
        )
    return findings


def _findings_from_db(db: Session, report: OperationalReport) -> list[RuleFinding]:
    rows = (
        db.query(OperationalFinding)
        .filter(OperationalFinding.report_id == report.id)
        .all()
    )
    if not rows:
        return _findings_from_report(report)
    return [
        RuleFinding(
            finding_type=f.finding_type,
            title=f.title,
            detail=f.detail,
            severity=f.severity,
            confidence=f.confidence,
            business_impact=f.business_impact,
            department=f.department,
            category=f.category,
            suggested_action=f.suggested_action or "",
        )
        for f in rows
    ]


class ReportInsightsBundle:
    def __init__(
        self,
        data_digest: dict,
        domain_insights: list[dict],
        data_coverage: dict,
        analysis_metadata: dict,
        hydrated: bool = False,
    ):
        self.data_digest = data_digest
        self.domain_insights = domain_insights
        self.data_coverage = data_coverage
        self.analysis_metadata = analysis_metadata
        self.hydrated = hydrated


def hydrate_report_insights(
    db: Session,
    report: OperationalReport,
) -> ReportInsightsBundle:
    """Return persisted insight fields, computing on read for legacy reports."""
    if report.data_digest is not None:
        digest = digest_from_dict(report.data_digest)
        coverage = report.data_coverage or (build_data_coverage(digest) if digest else {})
        insights = report.domain_insights or []
        metadata = report.analysis_metadata or _legacy_metadata(report, coverage)
        return ReportInsightsBundle(
            data_digest=report.data_digest,
            domain_insights=insights,
            data_coverage=coverage,
            analysis_metadata=metadata,
            hydrated=False,
        )

    digest = build_data_digest(db, report.org_id)
    findings = _findings_from_db(db, report)
    coverage = build_data_coverage(digest)
    insights = [i.to_dict() for i in build_domain_insights(digest, findings)]
    metadata = _legacy_metadata(report, coverage)
    return ReportInsightsBundle(
        data_digest=digest.to_dict(),
        domain_insights=insights,
        data_coverage=coverage,
        analysis_metadata=metadata,
        hydrated=True,
    )


def _legacy_metadata(report: OperationalReport, coverage: dict[str, bool]) -> dict:
    domains = [k for k, v in coverage.items() if v]
    finding_count = len(report.financial_findings or []) + len(report.operational_findings or [])
    return AnalysisMetadataOut(
        narration="legacy",
        finding_count=finding_count,
        data_domains_present=domains,
    ).model_dump()


def validate_insights_invariant(data_digest: dict, domain_insights: list) -> None:
    """Acceptance check: digest with data must produce KPI-relevant insights."""
    digest = digest_from_dict(data_digest) or DataDigest()
    if not digest_has_data(digest):
        return
    if not domain_insights:
        raise ValueError(
            "Insight invariant violated: digest has data but domain_insights is empty"
        )


def serialize_insights_for_api(bundle: ReportInsightsBundle) -> dict:
    validate_insights_invariant(bundle.data_digest, bundle.domain_insights)
    digest = DataDigestOut.model_validate(bundle.data_digest).model_dump()
    insights = [DomainInsightOut.model_validate(i).model_dump() for i in bundle.domain_insights]
    coverage = DataCoverageOut.model_validate(bundle.data_coverage).model_dump()
    metadata = AnalysisMetadataOut.model_validate(bundle.analysis_metadata).model_dump()
    return {
        "data_digest": digest,
        "domain_insights": insights,
        "data_coverage": coverage,
        "analysis_metadata": metadata,
    }
