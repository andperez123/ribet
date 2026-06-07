from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models import IngestJob, OperationalFinding, OperationalMemory, OperationalReport, Organization
from app.services.digest import (
    build_data_coverage,
    build_data_digest,
    build_domain_insights,
    build_executive_summary,
    domains_for_report_type,
)
from app.services.events import emit_event
from app.services.health import build_trend_snapshot, compute_health, get_prior_snapshot
from app.services.memory import upsert_memory
from app.services.narrator import narrate_findings_batch
from app.services.report_insights import validate_insights_invariant
from app.services.rules.cross_sector import run_cross_sector_rules
from app.services.rules.runner import RuleFinding, run_rules, run_snapshot_delta_rules
from app.services.telemetry import track_stage
from app.services.improvements import build_improvement_notes
from app.services.series import append_series_snapshot, get_or_create_series, get_prior_series_snapshot
from app.services.transforms.snapshot import (
    build_operational_snapshot,
    get_prior_snapshot as get_prior_op_snapshot,
    snapshot_delta_strings,
)


def persist_findings(
    db: Session,
    org_id: UUID,
    job_id: UUID,
    report_id: UUID,
    findings: list[RuleFinding],
    narratives: dict[str, dict[str, str]] | None = None,
) -> None:
    narratives = narratives or {}
    for f in findings:
        extra = narratives.get(f.fingerprint, {})
        db.add(
            OperationalFinding(
                org_id=org_id,
                job_id=job_id,
                report_id=report_id,
                finding_type=f.finding_type,
                title=f.title,
                detail=f.detail,
                severity=f.severity,
                confidence=f.confidence,
                business_impact=f.business_impact,
                department=f.department,
                category=f.category,
                fingerprint=f.fingerprint,
                suggested_action=extra.get("recommendation") or f.suggested_action,
                narrative=extra.get("narrative"),
                recommendation=extra.get("recommendation"),
            )
        )


def _merge_narratives_into_dicts(
    finding_dicts: list[dict],
    narratives: dict[str, dict[str, str]],
) -> list[dict]:
    merged: list[dict] = []
    for d in finding_dicts:
        row = dict(d)
        extra = narratives.get(row.get("fingerprint", ""), {})
        if extra.get("narrative"):
            row["narrative"] = extra["narrative"]
        if extra.get("recommendation"):
            row["recommendation"] = extra["recommendation"]
            row["suggested_action"] = extra["recommendation"]
        merged.append(row)
    return merged


def _analysis_metadata_from_narration(
    narration,
    finding_count: int,
    coverage: dict[str, bool],
) -> dict:
    domains = [k for k, v in coverage.items() if v and k in ("ar", "ap", "gl", "inventory")]
    if narration.skipped:
        status = "skipped"
    elif narration.failed:
        status = "failed"
    else:
        status = "completed"
    narrated = len([k for k in narration.narratives if k != "__executive__"])
    return {
        "narration": status,
        "model": narration.model_name,
        "finding_count": finding_count,
        "narrated_count": narrated,
        "data_domains_present": domains,
        "duration_ms": narration.duration_ms or None,
    }


def generate_report(
    db: Session,
    org_id: UUID,
    job_ids: list[UUID],
    period: str | None = None,
) -> OperationalReport:
    job_id = job_ids[0] if job_ids else None
    period_label = period or datetime.now(timezone.utc).strftime("%Y-%m")
    trigger_job = db.get(IngestJob, job_id) if job_id else None
    report_domains = domains_for_report_type(trigger_job.report_type if trigger_job else None)
    primary_domain = None
    if trigger_job and trigger_job.report_type:
        primary_domain = {
            "ar_aging": "ar",
            "ap_aging": "ap",
            "gl_detail": "gl",
            "inventory": "inventory",
        }.get(trigger_job.report_type)

    with track_stage(db, "rules", org_id=org_id, job_id=job_id):
        findings = run_rules(
            db,
            org_id,
            period=period_label,
            source_job_ids=job_ids or None,
            domains=report_domains,
        )

    org = db.get(Organization, org_id)
    org_name = org.name if org else "Organization"

    report = OperationalReport(org_id=org_id, job_ids=[str(j) for j in job_ids], period_label=period_label)
    db.add(report)
    db.flush()
    prior_op = get_prior_op_snapshot(db, org_id, exclude_period=period_label)
    op_snap = build_operational_snapshot(
        db,
        org_id,
        period_label,
        job_ids[0] if job_ids else org_id,
        100,
        "Stable",
    )

    with track_stage(db, "rules_delta", org_id=org_id, job_id=job_id):
        findings.extend(run_snapshot_delta_rules(db, org_id))
    with track_stage(db, "rules_cross_sector", org_id=org_id, job_id=job_id):
        findings.extend(run_cross_sector_rules(db, org_id, op_snap, findings))
    upsert_memory(db, org_id, findings)

    health_snap = compute_health(db, org_id, findings, report.id)
    op_snap.health_score = health_snap.score
    op_snap.health_status = health_snap.status

    prior_health = get_prior_snapshot(db, org_id, exclude_id=health_snap.id)
    trends = build_trend_snapshot(health_snap, prior_health, findings)
    trends = list(trends) + snapshot_delta_strings(op_snap, prior_op)

    digest = build_data_digest(
        db,
        org_id,
        period=period_label,
        source_job_ids=job_ids or None,
        domains=report_domains,
    )
    coverage = build_data_coverage(digest, primary_domain=primary_domain)
    domain_insights = [i.to_dict() for i in build_domain_insights(digest, findings)]

    validate_insights_invariant(digest.to_dict(), domain_insights)

    if settings.ribet_narration.lower() == "on" and settings.openai_api_key:
        emit_event(
            db,
            "narration_started",
            org_id=org_id,
            job_id=job_id,
            metadata={"finding_count": len(findings)},
        )
        db.commit()

    narration = narrate_findings_batch(findings, org_name, op_snap, prior_op, digest=digest)
    narr_meta = {
        "duration_ms": narration.duration_ms,
        "model_name": narration.model_name,
        "token_usage": narration.token_usage,
        "finding_count": len(findings),
        "narrated_count": len(narration.narratives),
        "skipped": narration.skipped,
    }
    if narration.failed:
        emit_event(
            db,
            "narration_failed",
            org_id=org_id,
            job_id=job_id,
            metadata={**narr_meta, "error_type": narration.error_type},
        )
        db.commit()
    elif not narration.skipped:
        emit_event(
            db,
            "narration_completed",
            org_id=org_id,
            job_id=job_id,
            metadata=narr_meta,
        )
        db.commit()
    narratives = narration.narratives

    financial = _merge_narratives_into_dicts(
        [f.to_dict() for f in findings if f.category == "financial"],
        narratives,
    )
    operational = _merge_narratives_into_dicts(
        [f.to_dict() for f in findings if f.category == "operational"],
        narratives,
    )
    risk = _merge_narratives_into_dicts(
        [
            f.to_dict()
            for f in findings
            if f.severity in ("high", "critical") or f.category == "risk"
        ],
        narratives,
    )

    recurring = (
        db.query(OperationalMemory)
        .filter(OperationalMemory.org_id == org_id, OperationalMemory.occurrence_count > 1)
        .all()
    )
    for mem in recurring:
        risk.append(
            {
                "title": mem.title,
                "detail": f"Detected {mem.occurrence_count} times. Last seen {mem.last_seen_at.isoformat()}.",
                "severity": mem.severity_peak,
                "category": "risk",
                "finding_type": mem.finding_type,
            }
        )

    analyst_summary: str | None = None
    if narratives.get("__executive__"):
        analyst_summary = narratives["__executive__"].get("narrative") or None

    executive = build_executive_summary(digest, findings)
    management_questions = list(narration.management_questions)

    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    seen_actions: set[str] = set()
    actions: list[str] = []
    for f in sorted(findings, key=lambda x: severity_rank.get(x.severity, 0), reverse=True):
        act = f.suggested_action
        if act and act not in seen_actions:
            seen_actions.add(act)
            actions.append(act)

    report.executive_summary = executive
    report.financial_findings = financial
    report.operational_findings = operational
    report.risk_areas = risk
    report.suggested_actions = actions
    report.trend_snapshot = trends
    report.health_score = health_snap.score
    report.health_status = health_snap.status
    report.data_digest = digest.to_dict()
    report.domain_insights = domain_insights
    report.data_coverage = coverage
    report.analysis_metadata = _analysis_metadata_from_narration(
        narration, len(findings), coverage
    )
    report.analyst_summary = analyst_summary
    report.management_questions = management_questions

    if job_ids:
        with track_stage(
            db,
            "report_persist",
            org_id=org_id,
            job_id=job_id,
            report_id=report.id,
            extra={"finding_count": len(findings)},
        ):
            persist_findings(db, org_id, job_ids[0], report.id, findings, narratives)

    if job_id:
        job = db.get(IngestJob, job_id)
        if job and job.schema_fingerprint and job.report_type:
            series = get_or_create_series(
                db, org_id, job.report_type, job.schema_fingerprint, job
            )
            prior_snap = get_prior_series_snapshot(db, series.id)
            kpi_summary = {
                "ar_total": digest.ar_total,
                "ar_over_90_pct": digest.ar_over_90_pct,
                "ap_total": digest.ap_total,
                "health_score": health_snap.score,
                "health_status": health_snap.status,
                "vendor_concentration": op_snap.vendor_concentration,
            }
            improvement_notes = build_improvement_notes(kpi_summary, prior_snap)
            report.improvement_notes = improvement_notes
            append_series_snapshot(
                db,
                org_id=org_id,
                series=series,
                period=period_label,
                job_id=job_id,
                report_id=report.id,
                content_hash=job.content_hash,
                kpi_summary=kpi_summary,
                improvement_notes=improvement_notes,
            )

    db.commit()
    db.refresh(report)
    emit_event(
        db,
        "report_generated",
        org_id=org_id,
        report_id=report.id,
        job_id=job_id,
        metadata={
            "health_score": report.health_score,
            "finding_count": len(findings),
            "narration_failed": narration.failed,
            "narration_ms": narration.duration_ms,
            "data_domains": [k for k, v in coverage.items() if v],
        },
    )
    db.commit()
    return report


def delete_report(db: Session, org_id: UUID, report_id: UUID) -> bool:
    """Delete a report and its dependent rows. Returns False if not found."""
    from sqlalchemy import delete, update

    from app.models import (
        HealthSnapshot,
        IngestJob,
        OperationalFinding,
        ProductEvent,
        SeriesSnapshot,
    )

    report = db.get(OperationalReport, report_id)
    if not report or report.org_id != org_id:
        return False

    db.execute(
        delete(OperationalFinding).where(OperationalFinding.report_id == report_id)
    )
    db.execute(delete(HealthSnapshot).where(HealthSnapshot.report_id == report_id))
    db.execute(delete(ProductEvent).where(ProductEvent.report_id == report_id))
    db.execute(delete(SeriesSnapshot).where(SeriesSnapshot.report_id == report_id))
    db.execute(
        update(IngestJob)
        .where(IngestJob.report_id == report_id)
        .values(report_id=None)
    )
    db.delete(report)
    db.commit()
    return True
