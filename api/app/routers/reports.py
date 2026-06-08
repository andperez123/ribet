from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_organization, verify_api_key
from app.models import OperationalFinding, OperationalReport, Organization
from app.schemas import FindingOut, OperationalReportOut, ReportSummary, ReportsListResponse
from app.services.pdf_export import render_report_pdf
from app.services.report import delete_report
from app.services.report_insights import hydrate_report_insights, serialize_insights_for_api

router = APIRouter(prefix="/v1", tags=["reports"])


def _report_to_out(db: Session, r: OperationalReport) -> OperationalReportOut:
    bundle = hydrate_report_insights(db, r)
    insight_fields = serialize_insights_for_api(bundle)
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
        data_digest=insight_fields["data_digest"],
        domain_insights=insight_fields["domain_insights"],
        data_coverage=insight_fields["data_coverage"],
        analysis_metadata=insight_fields["analysis_metadata"],
        analyst_summary=r.analyst_summary,
        management_questions=r.management_questions or [],
        period_label=r.period_label,
        improvement_notes=r.improvement_notes or [],
        report_contract=r.report_contract,
    )


@router.get("/reports", response_model=ReportsListResponse)
def list_reports(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
    limit: int = 20,
):
    reports = (
        db.query(OperationalReport)
        .filter(OperationalReport.org_id == org.id)
        .order_by(OperationalReport.generated_at.desc())
        .limit(limit)
        .all()
    )
    summaries: list[ReportSummary] = []
    for r in reports:
        finding_count = (
            db.query(func.count(OperationalFinding.id))
            .filter(OperationalFinding.report_id == r.id)
            .scalar()
            or 0
        )
        summaries.append(
            ReportSummary(
                id=r.id,
                generated_at=r.generated_at.isoformat() if r.generated_at else "",
                health_score=r.health_score,
                health_status=r.health_status,
                finding_count=finding_count,
            )
        )
    return ReportsListResponse(reports=summaries)


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
    return _report_to_out(db, report)


@router.get("/reports/{report_id}/pdf")
def get_report_pdf(
    report_id: UUID,
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    pdf_bytes = render_report_pdf(db, org.id, report_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="ribet-report-{report_id}.pdf"'
        },
    )


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
    return _report_to_out(db, report)


@router.delete("/reports/{report_id}")
def remove_report(
    report_id: UUID,
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    if not delete_report(db, org.id, report_id):
        raise HTTPException(status_code=404, detail="Report not found")
    return {"deleted": True, "id": str(report_id)}


@router.get("/findings", response_model=list[FindingOut])
def list_findings(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
    limit: int = 50,
    report_id: UUID | None = Query(default=None),
):
    q = db.query(OperationalFinding).filter(OperationalFinding.org_id == org.id)
    if report_id is not None:
        q = q.filter(OperationalFinding.report_id == report_id)
    rows = q.order_by(OperationalFinding.detected_at.desc()).limit(limit).all()

    gap_by_type: dict[str, str] = {}
    if report_id is not None:
        report = db.get(OperationalReport, report_id)
        if report and report.report_contract:
            for item in report.report_contract.get("action_items") or []:
                ft = item.get("finding_type")
                gap = item.get("gap_recommendation")
                if ft and gap:
                    gap_by_type[ft] = gap

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
            narrative=f.narrative,
            recommendation=f.recommendation,
            gap_recommendation=gap_by_type.get(f.finding_type),
            detected_at=f.detected_at.isoformat() if f.detected_at else "",
        )
        for f in rows
    ]
