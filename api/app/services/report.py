from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import OperationalFinding, OperationalMemory, OperationalReport
from app.services.health import build_trend_snapshot, compute_health, get_prior_snapshot
from app.services.memory import upsert_memory
from app.services.rules.runner import RuleFinding, run_rules


def persist_findings(
    db: Session,
    org_id: UUID,
    job_id: UUID,
    report_id: UUID,
    findings: list[RuleFinding],
) -> None:
    for f in findings:
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
                suggested_action=f.suggested_action,
            )
        )


def generate_report(
    db: Session,
    org_id: UUID,
    job_ids: list[UUID],
) -> OperationalReport:
    findings = run_rules(db, org_id)
    upsert_memory(db, org_id, findings)

    report = OperationalReport(org_id=org_id, job_ids=job_ids)
    db.add(report)
    db.flush()

    snapshot = compute_health(db, org_id, findings, report.id)
    prior = get_prior_snapshot(db, org_id, exclude_id=snapshot.id)
    trends = build_trend_snapshot(snapshot, prior, findings)

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
    report.health_score = snapshot.score
    report.health_status = snapshot.status

    if job_ids:
        persist_findings(db, org_id, job_ids[0], report.id, findings)

    db.commit()
    db.refresh(report)
    return report
