from __future__ import annotations

"""Weekly operational brief email via Resend."""

import base64
import logging
from pathlib import Path
from uuid import UUID

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.config import settings
from app.models import OperationalFinding, OperationalReport, Organization
from app.services.pdf_export import render_report_pdf

logger = logging.getLogger("ribet.email")

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _recipients_for_org(org: Organization) -> list[str]:
    if org.email_recipients:
        return list(org.email_recipients)
    if settings.default_brief_recipient:
        return [settings.default_brief_recipient]
    return []


def send_weekly_brief(db: Session, org_id: UUID, report_id: UUID | None = None) -> bool:
    if not settings.resend_api_key:
        logger.warning("resend_skipped no_api_key org_id=%s", org_id)
        return False

    org = db.get(Organization, org_id)
    if not org:
        return False

    recipients = _recipients_for_org(org)
    if not recipients:
        logger.warning("resend_skipped no_recipients org_id=%s", org_id)
        return False

    q = db.query(OperationalReport).filter(OperationalReport.org_id == org_id)
    if report_id:
        report = db.get(OperationalReport, report_id)
    else:
        report = q.order_by(OperationalReport.generated_at.desc()).first()
    if not report:
        return False

    findings = (
        db.query(OperationalFinding)
        .filter(OperationalFinding.report_id == report.id)
        .order_by(OperationalFinding.detected_at.desc())
        .limit(5)
        .all()
    )
    finding_rows = [
        {
            "title": f.title,
            "detail": f.narrative or f.detail,
            "severity": f.severity,
        }
        for f in findings
    ]
    if not finding_rows and report.executive_summary:
        finding_rows = [{"title": s, "detail": "", "severity": ""} for s in report.executive_summary[:5]]

    report_url = f"{settings.ribet_app_url.rstrip('/')}/dashboard/reports/{report.id}"
    html = _env.get_template("weekly_brief.html").render(
        org_name=org.name,
        generated_at=report.generated_at.isoformat() if report.generated_at else "",
        health_score=report.health_score,
        health_status=report.health_status,
        findings=finding_rows,
        report_url=report_url,
    )

    attachments = []
    try:
        pdf_bytes = render_report_pdf(db, org_id, report.id)
        attachments.append(
            {
                "filename": f"ribet-report-{report.id}.pdf",
                "content": base64.b64encode(pdf_bytes).decode("ascii"),
            }
        )
    except Exception as e:
        logger.warning("pdf_attach_failed org_id=%s error=%s", org_id, e)

    import resend

    resend.api_key = settings.resend_api_key
    params: dict = {
        "from": settings.resend_from,
        "to": recipients,
        "subject": f"Ribet weekly brief — {org.name} (score {report.health_score})",
        "html": html,
    }
    if attachments:
        params["attachments"] = attachments

    resend.Emails.send(params)
    logger.info("brief_sent org_id=%s report_id=%s to=%s", org_id, report.id, recipients)
    return True


def send_briefs_for_active_orgs(db: Session) -> int:
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    org_ids = (
        db.query(OperationalReport.org_id)
        .filter(OperationalReport.generated_at >= cutoff)
        .distinct()
        .all()
    )
    sent = 0
    for (oid,) in org_ids:
        if send_weekly_brief(db, oid):
            sent += 1
    return sent
