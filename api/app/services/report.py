from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models import OperationalFinding, OperationalMemory, OperationalReport
from app.services.events import emit_event
from app.services.digest import build_data_digest, build_executive_summary
from app.services.health import build_trend_snapshot, compute_health, get_prior_snapshot
from app.services.memory import upsert_memory
from app.models import Organization
from app.services.narrator import narrate_findings_batch
from app.services.telemetry import track_stage
from app.services.rules.runner import RuleFinding, run_rules, run_snapshot_delta_rules
from app.services.rules.cross_sector import run_cross_sector_rules
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


def generate_report(
    db: Session,
    org_id: UUID,
    job_ids: list[UUID],
    period: str | None = None,
) -> OperationalReport:
    job_id = job_ids[0] if job_ids else None
    with track_stage(db, "rules", org_id=org_id, job_id=job_id):
        findings = run_rules(db, org_id)

    org = db.get(Organization, org_id)
    org_name = org.name if org else "Organization"

    report = OperationalReport(
        org_id=org_id, job_ids=[str(j) for j in job_ids]
    )
    db.add(report)
    db.flush()

    health_snap = compute_health(db, org_id, findings, report.id)
    prior_health = get_prior_snapshot(db, org_id, exclude_id=health_snap.id)
    trends = build_trend_snapshot(health_snap, prior_health, findings)

    period_label = period or datetime.now(timezone.utc).strftime("%Y-%m")
    prior_op = get_prior_op_snapshot(db, org_id, exclude_period=period_label)
    op_snap = build_operational_snapshot(
        db,
        org_id,
        period_label,
        job_ids[0] if job_ids else org_id,
        health_snap.score,
        health_snap.status,
    )
    with track_stage(db, "rules_delta", org_id=org_id, job_id=job_id):
        findings.extend(run_snapshot_delta_rules(db, org_id))
    with track_stage(db, "rules_cross_sector", org_id=org_id, job_id=job_id):
        findings.extend(run_cross_sector_rules(db, org_id, op_snap, findings))
    upsert_memory(db, org_id, findings)
    trends = list(trends) + snapshot_delta_strings(op_snap, prior_op)

    digest = build_data_digest(db, org_id)

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

    financial = [f.to_dict() for f in findings if f.category == "financial"]
    operational = [f.to_dict() for f in findings if f.category == "operational"]
    risk = [f.to_dict() for f in findings if f.severity in ("high", "critical") or f.category == "risk"]

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

    executive = build_executive_summary(digest, findings)
    if narratives.get("__executive__"):
        llm_exec = narratives["__executive__"].get("narrative")
        if llm_exec:
            executive = [llm_exec] + executive
    for q in narration.management_questions:
        executive.append(f"Question for management: {q}")

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
        },
    )
    db.commit()
    return report
