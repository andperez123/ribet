from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_organization, verify_api_key
from app.models import OperationalFinding, OperationalReport, Organization
from app.schemas import FindingOut, OperationalReportOut, ReportSummary, ReportsListResponse
from app.schemas.report_setup import (
    RegenerateRequest,
    ReportPatchIn,
    ReportSetupGetOut,
    ReportSetupPutIn,
    ReportSetupSnapshotOut,
)
from app.services.pdf_export import render_report_pdf
from app.services.report import (
    apply_narrative_overrides_to_report,
    delete_report,
    patch_report,
    regenerate_org_report,
)
from app.services.report_insights import hydrate_report_insights, serialize_insights_for_api
from app.services.evidence_pack import get_evidence_pack_for_report
from app.services.ai_analyst.runner import get_analyst_output_for_report
from app.services.report_context import (
    SetupValidationError,
    compute_setup_preview,
    draft_to_out,
    get_or_create_draft,
    get_report_sources,
    list_available_jobs,
    resolve_generation_context,
    save_draft,
    snapshot_dict_to_out,
    validate_source_jobs,
)
from app.services.report_context import _job_to_source_out

router = APIRouter(prefix="/v1", tags=["reports"])


def _report_to_out(db: Session, r: OperationalReport) -> OperationalReportOut:
    apply_narrative_overrides_to_report(r)
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
        evidence_pack=get_evidence_pack_for_report(db, r.id),
        analyst_output=get_analyst_output_for_report(db, r.id),
        generation_context=r.generation_context,
        sources=get_report_sources(db, r),
    )




@router.get("/reports/setup", response_model=ReportSetupGetOut)
def get_report_setup(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
    preview: bool = Query(default=False),
):
    draft = get_or_create_draft(db, org.id)
    db.commit()
    available = list_available_jobs(db, org.id)
    draft_out = draft_to_out(draft)
    warnings = validate_source_jobs(
        db,
        org.id,
        draft_out.source_job_ids,
        raise_on_warnings=False,
    ) if draft_out.source_job_ids else []
    preview_out = None
    if preview and draft_out.source_job_ids:
        preview_out = compute_setup_preview(db, org.id, draft_out.source_job_ids)
    return ReportSetupGetOut(
        draft=draft_out,
        available_jobs=[_job_to_source_out(j) for j in available],
        warnings=warnings,
        preview=preview_out,
    )


@router.get("/reports/setup/preview", response_model=ReportSetupGetOut)
def preview_report_setup(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
    job_ids: list[UUID] = Query(default=[]),
):
    draft = get_or_create_draft(db, org.id)
    selected = job_ids or draft_to_out(draft).source_job_ids
    warnings = validate_source_jobs(db, org.id, selected, raise_on_warnings=False) if selected else []
    preview_out = compute_setup_preview(db, org.id, selected) if selected else None
    return ReportSetupGetOut(
        draft=draft_to_out(draft),
        available_jobs=[_job_to_source_out(j) for j in list_available_jobs(db, org.id)],
        warnings=warnings,
        preview=preview_out,
    )


@router.put("/reports/setup", response_model=ReportSetupGetOut)
def put_report_setup(
    body: ReportSetupPutIn,
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    try:
        if body.source_job_ids is not None:
            validate_source_jobs(db, org.id, body.source_job_ids)
        draft = save_draft(
            db,
            org.id,
            source_job_ids=body.source_job_ids,
            manual_notes=body.manual_notes,
            excluded_finding_ids=body.excluded_finding_ids,
            evidence_overrides=body.evidence_overrides,
            narrative_overrides=body.narrative_overrides,
        )
        db.commit()
    except SetupValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    draft_out = draft_to_out(draft)
    warnings = validate_source_jobs(
        db,
        org.id,
        draft_out.source_job_ids,
        raise_on_warnings=False,
    ) if draft_out.source_job_ids else []
    return ReportSetupGetOut(
        draft=draft_out,
        available_jobs=[_job_to_source_out(j) for j in list_available_jobs(db, org.id)],
        warnings=warnings,
        preview=compute_setup_preview(db, org.id, draft_out.source_job_ids)
        if draft_out.source_job_ids
        else None,
    )


@router.get("/reports/{report_id}/setup", response_model=ReportSetupSnapshotOut)
def get_report_setup_snapshot(
    report_id: UUID,
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    report = db.get(OperationalReport, report_id)
    if not report or report.org_id != org.id:
        raise HTTPException(status_code=404, detail="Report not found")
    raw = report.generation_context or {}
    if not raw:
        raise HTTPException(status_code=404, detail="No setup snapshot for this report")
    try:
        snapshot = snapshot_dict_to_out(raw)
    except SetupValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ReportSetupSnapshotOut(
        snapshot=snapshot,
        sources=get_report_sources(db, report),
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


@router.patch("/reports/{report_id}", response_model=OperationalReportOut)
def update_report(
    report_id: UUID,
    body: ReportPatchIn,
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    report = patch_report(
        db,
        org.id,
        report_id,
        executive_summary=body.executive_summary,
        management_questions=body.management_questions,
        narrative_overrides=body.narrative_overrides,
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_out(db, report)


@router.post("/reports/regenerate", response_model=OperationalReportOut)
def regenerate_report(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
    body: RegenerateRequest = Body(default_factory=RegenerateRequest),
):
    payload = body
    if payload.mode == "ai_only" and not payload.source_job_ids:
        pass
    try:
        generation_context = resolve_generation_context(
            db,
            org.id,
            source_job_ids=payload.source_job_ids,
            manual_notes=payload.manual_notes,
            excluded_finding_ids=payload.excluded_finding_ids,
            evidence_overrides=payload.evidence_overrides,
            narrative_overrides=payload.narrative_overrides,
            regenerate_mode=payload.mode,
        )
        report = regenerate_org_report(db, org.id, generation_context=generation_context)
    except SetupValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
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
    report_id: Optional[UUID] = Query(default=None),
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
            finding_id=f.finding_id,
            finding_instance_id=f.finding_instance_id,
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
