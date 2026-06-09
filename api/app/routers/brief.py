from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_organization, verify_api_key
from app.models import OperationalFinding, OperationalReport, Organization
from app.schemas import WeeklyBrief
from app.services.digest import build_weekly_brief_sections
from app.services.report_insights import digest_from_dict, hydrate_report_insights
from app.services.rules.runner import RuleFinding

router = APIRouter(prefix="/v1/brief", tags=["brief"])


def _findings_for_report(db: Session, org_id: UUID, report: OperationalReport) -> list:
    rows = (
        db.query(OperationalFinding)
        .filter(
            OperationalFinding.org_id == org_id,
            OperationalFinding.report_id == report.id,
        )
        .order_by(OperationalFinding.detected_at.desc())
        .all()
    )
    if rows:
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


@router.get("/weekly", response_model=WeeklyBrief)
def weekly_brief(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
    report_id: Optional[UUID] = Query(default=None),
):
    q = db.query(OperationalReport).filter(OperationalReport.org_id == org.id)
    if report_id is not None:
        report = q.filter(OperationalReport.id == report_id).first()
    else:
        report = q.order_by(OperationalReport.generated_at.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail="No data for brief")

    bundle = hydrate_report_insights(db, report)
    digest = digest_from_dict(bundle.data_digest)
    if digest is None:
        from app.services.digest import DataDigest

        digest = DataDigest()

    findings = _findings_for_report(db, org.id, report)
    sections = build_weekly_brief_sections(
        digest,
        findings,
        bundle.data_coverage,
        report.trend_snapshot,
    )

    return WeeklyBrief(org_id=org.id, period="weekly", sections=sections)
