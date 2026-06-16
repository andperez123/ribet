from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import IngestJob, OperationalReport, OperationalReportSourceJob, ReportContextDraft
from app.schemas.report_setup import (
    CONTEXT_SCHEMA_VERSION,
    BlockedAnalysisOut,
    ReportGenerationSnapshotOut,
    ReportSetupDraftOut,
    ReportSourceJobOut,
    SetupPreviewOut,
    SetupWarningOut,
)
from app.services.digest import domains_for_report_type
from app.services.graph.confidence import compute_analysis_confidence
from app.services.graph.coverage import COVERAGE_SPECS, GraphCoverage, CoverageItem
from app.services.report_contract import REPORT_TYPE_LABELS

REPORT_TYPE_TO_DOMAIN: dict[str, str] = {
    "ar_aging": "ar",
    "ap_aging": "ap",
    "gl_detail": "gl",
    "gl_trial_balance": "gl",
    "inventory": "inventory",
    "purchase_orders": "orders",
    "sales_orders": "sales",
}

LOW_MAPPING_CONFIDENCE = 0.7
MIN_ROW_COUNT = 1

BLOCKED_ANALYSIS_SPECS: list[dict] = [
    {
        "analysis_name": "AR concentration & aging risk",
        "reason_code": "missing_ar_aging",
        "requires_report_types": ["ar_aging"],
        "requires_uploads": ["AR Aging"],
    },
    {
        "analysis_name": "AP vendor concentration",
        "reason_code": "missing_ap_aging",
        "requires_report_types": ["ap_aging"],
        "requires_uploads": ["AP Aging"],
    },
    {
        "analysis_name": "Inventory health",
        "reason_code": "missing_inventory",
        "requires_report_types": ["inventory"],
        "requires_uploads": ["Inventory"],
    },
    {
        "analysis_name": "GL adjustment signals",
        "reason_code": "missing_gl_detail",
        "requires_report_types": ["gl_detail", "gl_trial_balance"],
        "requires_uploads": ["GL Detail or GL Trial Balance"],
    },
    {
        "analysis_name": "Vendor fulfillment analysis",
        "reason_code": "missing_purchase_orders",
        "requires_report_types": ["purchase_orders"],
        "requires_uploads": ["Purchase Orders"],
    },
    {
        "analysis_name": "Sales backlog analysis",
        "reason_code": "missing_sales_orders",
        "requires_report_types": ["sales_orders"],
        "requires_uploads": ["Open Sales Orders"],
    },
    {
        "analysis_name": "Cash pressure diagnosis",
        "reason_code": "missing_cross_domain",
        "requires_report_types": ["ar_aging", "ap_aging", "purchase_orders", "sales_orders"],
        "requires_uploads": ["AR Aging", "AP Aging", "Purchase Orders", "Open Sales Orders"],
    },
]


@dataclass
class ReportGenerationContext:
    context_schema_version: int = CONTEXT_SCHEMA_VERSION
    source_job_ids: list[UUID] = field(default_factory=list)
    period_label: str | None = None
    domains: list[str] | None = None
    manual_notes: str | None = None
    excluded_finding_ids: list[str] = field(default_factory=list)
    evidence_overrides: dict = field(default_factory=dict)
    narrative_overrides: dict = field(default_factory=dict)
    regenerate_mode: str = "full"
    submitted_at: datetime | None = None
    submitted_by_user_id: UUID | None = None
    source_context_hash: str | None = None


class SetupValidationError(ValueError):
    def __init__(self, message: str, code: str = "invalid_setup"):
        super().__init__(message)
        self.code = code


def _uuid_list(raw: list) -> list[UUID]:
    out: list[UUID] = []
    for item in raw or []:
        out.append(UUID(str(item)))
    return out


def _job_to_source_out(job: IngestJob) -> ReportSourceJobOut:
    rt = job.report_type
    return ReportSourceJobOut(
        id=job.id,
        file_name=job.file_name,
        report_type=rt,
        detected_period=job.detected_period,
        row_count=job.row_count,
        status=job.status,
        report_id=job.report_id,
        mapping_confidence=job.mapping_confidence,
        created_at=job.created_at.isoformat() if job.created_at else None,
        report_type_label=REPORT_TYPE_LABELS.get(rt or "", rt),
    )


def list_available_jobs(db: Session, org_id: UUID) -> list[IngestJob]:
    return (
        db.query(IngestJob)
        .filter(IngestJob.org_id == org_id, IngestJob.status == "done")
        .order_by(IngestJob.created_at.desc())
        .all()
    )


def default_source_job_ids(db: Session, org_id: UUID) -> list[UUID]:
    return [j.id for j in list_available_jobs(db, org_id)]


def get_or_create_draft(db: Session, org_id: UUID) -> ReportContextDraft:
    draft = db.get(ReportContextDraft, org_id)
    if draft:
        return draft
    job_ids = default_source_job_ids(db, org_id)
    draft = ReportContextDraft(
        org_id=org_id,
        context_schema_version=CONTEXT_SCHEMA_VERSION,
        source_job_ids=[str(j) for j in job_ids],
    )
    db.add(draft)
    db.flush()
    return draft


def draft_to_out(draft: ReportContextDraft) -> ReportSetupDraftOut:
    if draft.context_schema_version != CONTEXT_SCHEMA_VERSION:
        raise SetupValidationError(
            "Report setup schema is outdated. Please refresh the page.",
            code="schema_version_mismatch",
        )
    return ReportSetupDraftOut(
        context_schema_version=draft.context_schema_version,
        source_job_ids=_uuid_list(draft.source_job_ids or []),
        manual_notes=draft.manual_notes,
        excluded_finding_ids=list(draft.excluded_finding_ids or []),
        evidence_overrides=dict(draft.evidence_overrides or {}),
        narrative_overrides=dict(draft.narrative_overrides or {}),
    )


def save_draft(
    db: Session,
    org_id: UUID,
    *,
    source_job_ids: list[UUID] | None = None,
    manual_notes: str | None = None,
    excluded_finding_ids: list[str] | None = None,
    evidence_overrides: dict | None = None,
    narrative_overrides: dict | None = None,
) -> ReportContextDraft:
    draft = get_or_create_draft(db, org_id)
    if source_job_ids is not None:
        validate_source_jobs(db, org_id, source_job_ids, raise_on_warnings=False)
        draft.source_job_ids = [str(j) for j in source_job_ids]
    if manual_notes is not None:
        draft.manual_notes = manual_notes.strip() or None
    if excluded_finding_ids is not None:
        draft.excluded_finding_ids = list(excluded_finding_ids)
    if evidence_overrides is not None:
        draft.evidence_overrides = dict(evidence_overrides)
    if narrative_overrides is not None:
        draft.narrative_overrides = dict(narrative_overrides)
    draft.context_schema_version = CONTEXT_SCHEMA_VERSION
    db.flush()
    return draft


def validate_source_jobs(
    db: Session,
    org_id: UUID,
    job_ids: list[UUID],
    *,
    raise_on_warnings: bool = False,
) -> list[SetupWarningOut]:
    warnings: list[SetupWarningOut] = []

    if not job_ids:
        raise SetupValidationError("Select at least one upload to generate a report.")

    jobs: list[IngestJob] = []
    for jid in job_ids:
        job = db.get(IngestJob, jid)
        if not job:
            raise SetupValidationError(f"Unknown upload: {jid}")
        if job.org_id != org_id:
            raise SetupValidationError("Upload belongs to another organization.")
        if job.status != "done":
            raise SetupValidationError(
                f"Upload {job.file_name} is not ready (status: {job.status})."
            )
        jobs.append(job)

    periods = {j.detected_period for j in jobs if j.detected_period}
    if len(periods) > 1:
        warnings.append(
            SetupWarningOut(
                code="conflicting_periods",
                message=f"Selected uploads span multiple periods: {', '.join(sorted(periods))}.",
            )
        )

    domain_counts: dict[str, list[str]] = {}
    for job in jobs:
        domain = REPORT_TYPE_TO_DOMAIN.get(job.report_type or "")
        if domain:
            domain_counts.setdefault(domain, []).append(job.file_name)

    for domain, files in domain_counts.items():
        if len(files) > 1:
            warnings.append(
                SetupWarningOut(
                    code="duplicate_domain",
                    message=(
                        f"Multiple {domain.upper()} uploads selected ({', '.join(files)}). "
                        "Consider using one per domain."
                    ),
                )
            )

    jobs_without_period = [j.file_name for j in jobs if not j.detected_period]
    if jobs_without_period:
        warnings.append(
            SetupWarningOut(
                code="no_detected_period",
                message=(
                    f"No period detected for: {', '.join(jobs_without_period)}. "
                    "Report will use the current month as the period label."
                ),
            )
        )

    for job in jobs:
        if job.mapping_confidence is not None and job.mapping_confidence < LOW_MAPPING_CONFIDENCE:
            warnings.append(
                SetupWarningOut(
                    code="low_mapping_confidence",
                    message=(
                        f"{job.file_name} has low mapping confidence "
                        f"({job.mapping_confidence:.0%}). Review column mapping before relying on findings."
                    ),
                )
            )
        if job.row_count is not None and job.row_count < MIN_ROW_COUNT:
            warnings.append(
                SetupWarningOut(
                    code="not_enough_rows",
                    message=f"{job.file_name} has very few rows ({job.row_count}). Analysis may be limited.",
                )
            )

    if raise_on_warnings and warnings:
        raise SetupValidationError(warnings[0].message, code=warnings[0].code)

    return warnings


def _report_types_from_jobs(jobs: list[IngestJob]) -> set[str]:
    return {j.report_type for j in jobs if j.report_type and j.report_type != "unknown"}


def _coverage_from_jobs(jobs: list[IngestJob]) -> GraphCoverage:
    report_types = _report_types_from_jobs(jobs)
    items: list[CoverageItem] = []
    for spec in COVERAGE_SPECS:
        rt = spec.get("report_type")
        covered = False
        if rt and rt in report_types:
            covered = True
        elif spec["key"] in report_types:
            covered = True
        items.append(
            CoverageItem(
                key=spec["key"],
                label=spec["label"],
                sector=spec["sector"],
                covered=covered,
                uploadable=spec["uploadable"],
            )
        )
    return GraphCoverage(items=items, report_types=report_types)


def _domains_from_jobs(jobs: list[IngestJob]) -> set[str]:
    domains: set[str] = set()
    for job in jobs:
        job_domains = domains_for_report_type(job.report_type)
        if job_domains:
            domains.update(job_domains)
    return domains


def compute_setup_preview(
    db: Session,
    org_id: UUID,
    job_ids: list[UUID],
) -> SetupPreviewOut:
    warnings = validate_source_jobs(db, org_id, job_ids, raise_on_warnings=False)
    jobs = [db.get(IngestJob, jid) for jid in job_ids]
    jobs = [j for j in jobs if j is not None]

    coverage = _coverage_from_jobs(jobs)
    confidence = compute_analysis_confidence(coverage)
    domains = sorted(_domains_from_jobs(jobs))
    sectors = sorted({item.sector for item in coverage.understood if item.uploadable})

    report_types = _report_types_from_jobs(jobs)
    blocked: list[BlockedAnalysisOut] = []

    for spec in BLOCKED_ANALYSIS_SPECS:
        required = set(spec["requires_report_types"])
        if required.intersection(report_types):
            continue
        blocked.append(
            BlockedAnalysisOut(
                analysis_name=spec["analysis_name"],
                reason_code=spec["reason_code"],
                reason=f"Requires {', '.join(spec['requires_uploads'])}.",
                requires_uploads=list(spec["requires_uploads"]),
            )
        )

    for job in jobs:
        if not job.detected_period:
            blocked.append(
                BlockedAnalysisOut(
                    analysis_name=f"Period-scoped trends for {job.file_name}",
                    reason_code="no_period_detected",
                    reason="No accounting period detected for this upload.",
                    requires_uploads=[],
                )
            )
        if job.mapping_confidence is not None and job.mapping_confidence < LOW_MAPPING_CONFIDENCE:
            blocked.append(
                BlockedAnalysisOut(
                    analysis_name=f"High-confidence findings for {job.file_name}",
                    reason_code="low_mapping_confidence",
                    reason="Column mapping confidence is below the recommended threshold.",
                    requires_uploads=[],
                )
            )
        if job.row_count is not None and job.row_count < MIN_ROW_COUNT:
            blocked.append(
                BlockedAnalysisOut(
                    analysis_name=f"Statistical signals from {job.file_name}",
                    reason_code="not_enough_rows",
                    reason="Upload has too few rows for reliable pattern detection.",
                    requires_uploads=[],
                )
            )

    return SetupPreviewOut(
        domains_covered=domains,
        sectors_covered=sectors,
        analysis_confidence=confidence.score,
        blocked_analyses=blocked,
        warnings=warnings,
    )


def canonical_context_payload(context: ReportGenerationContext) -> dict:
    return {
        "context_schema_version": context.context_schema_version,
        "source_job_ids": sorted(str(j) for j in context.source_job_ids),
        "period_label": context.period_label,
        "domains": sorted(context.domains or []) if context.domains else None,
        "manual_notes": context.manual_notes,
        "excluded_finding_ids": sorted(context.excluded_finding_ids or []),
        "evidence_overrides": context.evidence_overrides or {},
        "narrative_overrides": context.narrative_overrides or {},
        "regenerate_mode": context.regenerate_mode,
    }


def compute_source_context_hash(context: ReportGenerationContext) -> str:
    payload = json.dumps(canonical_context_payload(context), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def resolve_generation_context(
    db: Session,
    org_id: UUID,
    *,
    source_job_ids: list[UUID] | None = None,
    manual_notes: str | None = None,
    excluded_finding_ids: list[str] | None = None,
    evidence_overrides: dict | None = None,
    narrative_overrides: dict | None = None,
    regenerate_mode: str = "full",
    submitted_by_user_id: UUID | None = None,
) -> ReportGenerationContext:
    draft = get_or_create_draft(db, org_id)
    job_ids = source_job_ids if source_job_ids is not None else _uuid_list(draft.source_job_ids or [])
    if not job_ids:
        available = list_available_jobs(db, org_id)
        if not available:
            raise ValueError("No successful uploads to build a report from")
        raise SetupValidationError("Select at least one upload to generate a report.")
    validate_source_jobs(db, org_id, job_ids)

    jobs = [db.get(IngestJob, jid) for jid in job_ids]
    jobs = [j for j in jobs if j is not None]
    periods = {j.detected_period for j in jobs if j.detected_period}
    period = periods.pop() if len(periods) == 1 else None
    domains = sorted(_domains_from_jobs(jobs))

    ctx = ReportGenerationContext(
        source_job_ids=job_ids,
        period_label=period,
        domains=domains or None,
        manual_notes=manual_notes if manual_notes is not None else draft.manual_notes,
        excluded_finding_ids=(
            excluded_finding_ids
            if excluded_finding_ids is not None
            else list(draft.excluded_finding_ids or [])
        ),
        evidence_overrides=(
            evidence_overrides
            if evidence_overrides is not None
            else dict(draft.evidence_overrides or {})
        ),
        narrative_overrides=(
            narrative_overrides
            if narrative_overrides is not None
            else dict(draft.narrative_overrides or {})
        ),
        regenerate_mode=regenerate_mode,
        submitted_at=datetime.now(timezone.utc),
        submitted_by_user_id=submitted_by_user_id,
    )
    ctx.source_context_hash = compute_source_context_hash(ctx)
    return ctx


def generation_context_to_snapshot_dict(context: ReportGenerationContext) -> dict:
    return {
        "context_schema_version": context.context_schema_version,
        "source_job_ids": [str(j) for j in context.source_job_ids],
        "period_label": context.period_label,
        "domains": context.domains,
        "submitted_at": context.submitted_at.isoformat() if context.submitted_at else None,
        "submitted_by_user_id": str(context.submitted_by_user_id)
        if context.submitted_by_user_id
        else None,
        "source_context_hash": context.source_context_hash,
        "regenerate_mode": context.regenerate_mode,
        "manual_notes": context.manual_notes,
        "excluded_finding_ids": list(context.excluded_finding_ids or []),
        "evidence_overrides": dict(context.evidence_overrides or {}),
        "narrative_overrides": dict(context.narrative_overrides or {}),
    }


def snapshot_dict_to_out(raw: dict) -> ReportGenerationSnapshotOut:
    if raw.get("context_schema_version", 1) != CONTEXT_SCHEMA_VERSION:
        raise SetupValidationError(
            "Report setup snapshot uses an unsupported schema version.",
            code="schema_version_mismatch",
        )
    return ReportGenerationSnapshotOut(
        context_schema_version=raw.get("context_schema_version", 1),
        source_job_ids=_uuid_list(raw.get("source_job_ids") or []),
        period_label=raw.get("period_label"),
        domains=raw.get("domains"),
        submitted_at=raw.get("submitted_at") or "",
        submitted_by_user_id=UUID(raw["submitted_by_user_id"])
        if raw.get("submitted_by_user_id")
        else None,
        source_context_hash=raw.get("source_context_hash") or "",
        regenerate_mode=raw.get("regenerate_mode") or "full",
        manual_notes=raw.get("manual_notes"),
        excluded_finding_ids=list(raw.get("excluded_finding_ids") or []),
        evidence_overrides=dict(raw.get("evidence_overrides") or {}),
        narrative_overrides=dict(raw.get("narrative_overrides") or {}),
    )


def persist_source_jobs(
    db: Session,
    report_id: UUID,
    job_ids: list[UUID],
    *,
    included_at: datetime | None = None,
) -> None:
    ts = included_at or datetime.now(timezone.utc)
    for jid in job_ids:
        db.add(
            OperationalReportSourceJob(
                report_id=report_id,
                ingest_job_id=jid,
                included_at=ts,
            )
        )


def link_included_jobs(db: Session, report_id: UUID, job_ids: list[UUID]) -> None:
    for jid in job_ids:
        job = db.get(IngestJob, jid)
        if job:
            job.report_id = report_id


def get_report_sources(db: Session, report: OperationalReport) -> list[ReportSourceJobOut]:
    rows = (
        db.query(OperationalReportSourceJob)
        .filter(OperationalReportSourceJob.report_id == report.id)
        .order_by(OperationalReportSourceJob.included_at.asc())
        .all()
    )
    if rows:
        out: list[ReportSourceJobOut] = []
        for row in rows:
            job = db.get(IngestJob, row.ingest_job_id)
            if job:
                out.append(_job_to_source_out(job))
        return out

    snapshot_ids = _uuid_list((report.generation_context or {}).get("source_job_ids") or [])
    if snapshot_ids:
        out = []
        for jid in snapshot_ids:
            job = db.get(IngestJob, jid)
            if job:
                out.append(_job_to_source_out(job))
        return out

    legacy_ids = _uuid_list(report.job_ids or [])
    out = []
    for jid in legacy_ids:
        job = db.get(IngestJob, jid)
        if job:
            out.append(_job_to_source_out(job))
    return out
