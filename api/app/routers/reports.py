from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_organization, verify_api_key
from app.models import OperationalFinding, OperationalReport, Organization
from app.schemas import FindingOut, OperationalReportOut

router = APIRouter(prefix="/v1", tags=["reports"])


def _report_to_out(r: OperationalReport) -> OperationalReportOut:
    return OperationalReportOut(
        id=r.id,
        org_id=r.org_id,
        executive_summary=r.executive_summary or [],
        financial_findings=r.financial_findings or [],
        operational_findings=r.operational_findings or [],
        risk_areas=r.risk_areas or [],
        suggested_actions=r.suggested_actions or [],
        trend_snapshot=r.trend_snapshot or [],
        health_score=r.health_score,
        health_status=r.health_status,
        generated_at=r.generated_at.isoformat() if r.generated_at else "",
    )


@router.get("/reports/latest", response_model=OperationalReportOut)
def get_latest_report(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    report = (
        db.query(OperationalReport)
        .filter(OperationalReport.org_id == org.id)
        .order_by(OperationalReport.generated_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No reports yet")
    return _report_to_out(report)


@router.get("/reports/{report_id}", response_model=OperationalReportOut)
def get_report(
    report_id: UUID,
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    report = db.get(OperationalReport, report_id)
    if not report or report.org_id != org.id:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_out(report)


@router.get("/findings", response_model=list[FindingOut])
def list_findings(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
    limit: int = 50,
):
    rows = (
        db.query(OperationalFinding)
        .filter(OperationalFinding.org_id == org.id)
        .order_by(OperationalFinding.detected_at.desc())
        .limit(limit)
        .all()
    )
    return [
        FindingOut(
            id=f.id,
            finding_type=f.finding_type,
            title=f.title,
            detail=f.detail,
            severity=f.severity,
            confidence=f.confidence,
            business_impact=f.business_impact,
            department=f.department,
            category=f.category,
            suggested_action=f.suggested_action,
            detected_at=f.detected_at.isoformat() if f.detected_at else "",
        )
        for f in rows
    ]
