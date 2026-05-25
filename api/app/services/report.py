from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import OperationalFinding, OperationalMemory, OperationalReport
from app.services.events import emit_event
from app.services.health import build_trend_snapshot, compute_health, get_prior_snapshot
from app.services.memory import upsert_memory
from app.models import Organization
from app.services.narrator import narrate_findings_batch
from app.services.rules.runner import RuleFinding, run_rules, run_snapshot_delta_rules
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
    findings.extend(run_snapshot_delta_rules(db, org_id))
    upsert_memory(db, org_id, findings)
    trends = list(trends) + snapshot_delta_strings(op_snap, prior_op)

    narratives = narrate_findings_batch(findings, org_name, op_snap, prior_op)

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

    executive = []
    for f in sorted(findings, key=lambda x: {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.severity, 0), reverse=True)[:5]:
        executive.append(f.title)

    if not executive:
        executive.append("No significant operational risks detected in current data.")

    actions = list({f.suggested_action for f in findings if f.suggested_action})

    report.executive_summary = executive
    report.financial_findings = financial
    report.operational_findings = operational
    report.risk_areas = risk
    report.suggested_actions = actions
    report.trend_snapshot = trends
    report.health_score = health_snap.score
    report.health_status = health_snap.status

    if job_ids:
        persist_findings(db, org_id, job_ids[0], report.id, findings, narratives)

    db.commit()
    db.refresh(report)
    emit_event(
        db,
        "report_generated",
        org_id=org_id,
        report_id=report.id,
        job_id=job_ids[0] if job_ids else None,
        metadata={"health_score": report.health_score, "finding_count": len(findings)},
    )
    db.commit()
    return report
