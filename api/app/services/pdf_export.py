"""Render operational reports as PDF via WeasyPrint."""

from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.models import OperationalFinding, OperationalReport, Organization

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def render_report_pdf(db: Session, org_id: UUID, report_id: UUID) -> bytes:
    report = db.get(OperationalReport, report_id)
    if not report or report.org_id != org_id:
        raise HTTPException(status_code=404, detail="Report not found")

    org = db.get(Organization, org_id)
    org_name = org.name if org else "Organization"

    findings = (
        db.query(OperationalFinding)
        .filter(OperationalFinding.report_id == report_id)
        .order_by(OperationalFinding.detected_at.desc())
        .limit(25)
        .all()
    )

    finding_rows = []
    for f in findings:
        detail = f.narrative or f.detail
        rec = f.recommendation or f.suggested_action
        finding_rows.append(
            {
                "title": f.title,
                "detail": detail,
                "severity": f.severity,
                "department": f.department,
                "suggested_action": rec,
            }
        )

    if not finding_rows:
        for block in (report.financial_findings or []) + (report.operational_findings or []):
            if isinstance(block, dict):
                finding_rows.append(
                    {
                        "title": block.get("title", ""),
                        "detail": block.get("detail", ""),
                        "severity": block.get("severity", ""),
                        "department": block.get("department", ""),
                        "suggested_action": block.get("suggested_action"),
                    }
                )

    html = _env.get_template("report.html").render(
        org_name=org_name,
        generated_at=report.generated_at.isoformat() if report.generated_at else "",
        health_score=report.health_score,
        health_status=report.health_status,
        executive_summary=report.executive_summary or ["No summary available."],
        findings=finding_rows[:15],
        suggested_actions=report.suggested_actions or [],
    )

    try:
        from weasyprint import HTML
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="PDF export unavailable (WeasyPrint not installed)",
        ) from e

    return HTML(string=html).write_pdf()
