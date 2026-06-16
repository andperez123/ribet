from __future__ import annotations

"""Org-level operational analysis — AI Controller entry point."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import OperationalReport
from app.services.gaps import get_open_gaps, sync_data_gaps
from app.services.graph.confidence import ConfidenceResult, compute_analysis_confidence
from app.services.graph.coverage import GraphCoverage, get_graph_coverage
from app.services.progress import recompute_org_progress
from app.services.report import generate_report
from app.services.report_context import ReportGenerationContext, compute_source_context_hash


@dataclass
class AnalysisResult:
    report: OperationalReport
    coverage: GraphCoverage
    confidence: ConfidenceResult


def run_operational_analysis(
    db: Session,
    org_id: UUID,
    trigger_job_id: UUID,
    period: str | None = None,
) -> AnalysisResult:
    """Transform is complete — enrich org model, analyze, report, and sync gaps."""
    generation_context = ReportGenerationContext(
        source_job_ids=[trigger_job_id],
        submitted_at=datetime.now(timezone.utc),
    )
    generation_context.source_context_hash = compute_source_context_hash(generation_context)

    report = generate_report(
        db,
        org_id,
        [trigger_job_id],
        period=period,
        generation_context=generation_context,
    )

    coverage = get_graph_coverage(db, org_id)
    confidence = compute_analysis_confidence(coverage)

    from app.models import OperationalFinding

    db_findings = (
        db.query(OperationalFinding)
        .filter(OperationalFinding.report_id == report.id)
        .all()
    )
    from app.services.rules.runner import RuleFinding

    rule_findings = [
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
        for f in db_findings
    ]

    sync_data_gaps(db, org_id, coverage, rule_findings)
    recompute_org_progress(db, org_id)
    db.commit()
    db.refresh(report)

    coverage = get_graph_coverage(db, org_id)
    confidence = compute_analysis_confidence(coverage)

    return AnalysisResult(report=report, coverage=coverage, confidence=confidence)
