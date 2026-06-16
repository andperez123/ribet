"""Guardrailed operational Q&A over the Evidence Pack."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models import EvidencePackRecord, OperationalReport
from app.schemas.evidence_pack import EvidencePack
from app.services.ai_analyst.client import call_openai_json, pack_to_json
from app.services.evidence_pack import build_evidence_pack

logger = logging.getLogger("ribet.chat")

CHAT_SYSTEM = """
You are Ribet's operations manager for an SMB manufacturer. Answer management questions using ONLY the Evidence Pack JSON.
NEVER invent numbers, PO numbers, invoice numbers, or dollar amounts not present in the pack.
Cite specific customer, vendor, invoice_id, and SKU names when they appear in row_details or findings.
When data is missing, say what upload would unlock the answer using analysis_boundaries.cannot_conclude.
Give specific, actionable advice: name the entity, dollar impact, and recommended next step with a deadline where possible.
Manual business context (manual_context field) may explain business conditions, but must not override numeric evidence.
Return JSON: {"answer": "...", "follow_up_questions": ["..."], "cited_finding_ids": ["..."], "confidence": "high|medium|low"}
"""


def _load_pack(db: Session, org_id: UUID, report_id: UUID | None) -> tuple[EvidencePack | None, OperationalReport | None]:
    report: OperationalReport | None = None
    if report_id:
        report = db.get(OperationalReport, report_id)
        if report and report.org_id != org_id:
            report = None
    if not report:
        report = (
            db.query(OperationalReport)
            .filter(OperationalReport.org_id == org_id)
            .order_by(OperationalReport.generated_at.desc())
            .first()
        )
    if not report:
        return None, None

    row = (
        db.query(EvidencePackRecord)
        .filter(EvidencePackRecord.report_id == report.id)
        .first()
    )
    if row and row.pack:
        try:
            return EvidencePack.model_validate(row.pack), report
        except Exception:
            pass
    return build_evidence_pack(db, report.id), report


def _row_details_dict(pack: EvidencePack) -> dict:
    if not pack.row_details:
        return {}
    return pack.row_details.model_dump()


def _deterministic_answer(pack: EvidencePack, question: str) -> dict:
    q = question.lower()
    parts: list[str] = []
    follow_ups: list[str] = []
    rows = _row_details_dict(pack)

    if "cash" in q or "receivable" in q or "ar" in q:
        ar = pack.metrics.get("ar", {})
        parts.append(
            f"Total receivables are ${ar.get('total_receivables', 0):,.0f}; "
            f"{ar.get('over_90_percent', 0):.1f}% (${ar.get('over_90_amount', 0):,.0f}) is over 90 days."
        )
        overdue = rows.get("ar_overdue_accounts") or []
        if overdue:
            top = overdue[0]
            parts.append(
                f"Largest overdue exposure: {top.get('customer')} invoice {top.get('invoice_id')} "
                f"at ${top.get('amount', 0):,.0f} ({top.get('days_overdue', 0)} days overdue)."
            )
        follow_ups.append("Which customers should we call this week?")

    if "vendor" in q or "payable" in q or "ap" in q or "po" in q or "purchase" in q:
        if "po" in q or "purchase" in q:
            orders = pack.metrics.get("orders", {})
            parts.append(
                f"Open POs: ${orders.get('open_po_total', 0):,.0f}; "
                f"{orders.get('late_po_count', 0)} late (${orders.get('late_po_total', 0):,.0f})."
            )
            late_pos = rows.get("late_purchase_orders") or []
            if late_pos:
                top = late_pos[0]
                parts.append(
                    f"Expedite PO {top.get('po_id')}: {top.get('vendor')} is "
                    f"{top.get('days_late', 0)} days late on ${top.get('open_amount', 0):,.0f} open."
                )
            follow_ups.append("Which POs should we expedite this week?")
        else:
            ap = pack.metrics.get("ap", {})
            parts.append(
                f"Open payables total ${ap.get('total_payables', 0):,.0f} "
                f"across {ap.get('vendor_count', 0)} vendors."
            )
            late = rows.get("ap_late_vendors") or []
            if late:
                top = late[0]
                parts.append(
                    f"Top late vendor: {top.get('vendor')} (${top.get('balance', 0):,.0f}, "
                    f"{top.get('days_overdue', 0)} days overdue)."
                )

    if "sales" in q or "ship" in q or "order" in q or "backlog" in q:
        sales = pack.metrics.get("sales", {})
        parts.append(
            f"Open sales orders: ${sales.get('open_so_total', 0):,.0f}; "
            f"{sales.get('past_due_count', 0)} past due (${sales.get('past_due_total', 0):,.0f})."
        )
        past_due = rows.get("past_due_sales_orders") or []
        if past_due:
            top = past_due[0]
            parts.append(
                f"SO {top.get('order_id')} for {top.get('customer')} is "
                f"{top.get('days_late', 0)} days past due with ${top.get('open_amount', 0):,.0f} open."
            )
        follow_ups.append("Which sales orders are blocking the most revenue?")

    if not parts:
        if pack.findings:
            top = sorted(pack.findings, key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(f.severity, 4))[0]
            parts.append(f"Top verified signal: {top.title}. {top.deterministic_action or ''}")
        else:
            parts.append(
                "Upload AR, AP, GL, or inventory exports to unlock specific answers. "
                + (pack.analysis_boundaries.cannot_conclude[0] if pack.analysis_boundaries.cannot_conclude else "")
            )

    return {
        "answer": " ".join(parts),
        "follow_up_questions": follow_ups[:3],
        "cited_finding_ids": [f.finding_id for f in pack.findings[:3] if f.finding_id],
        "confidence": "medium",
        "source": "deterministic",
    }


def answer_operational_question(
    db: Session,
    org_id: UUID,
    question: str,
    report_id: UUID | None = None,
) -> dict:
    question = (question or "").strip()
    if not question:
        raise ValueError("Question is required")

    pack, report = _load_pack(db, org_id, report_id)
    if not pack or not report:
        return {
            "answer": "No operational report is available yet. Upload ERP exports to generate your first report.",
            "follow_up_questions": ["What should I upload first?"],
            "cited_finding_ids": [],
            "confidence": "low",
            "source": "empty",
            "report_id": None,
        }

    if settings.ribet_narration.lower() != "on" or not settings.openai_api_key:
        result = _deterministic_answer(pack, question)
        result["report_id"] = str(report.id)
        result["narration_available"] = False
        return result

    user = json.dumps(
        {"question": question, "evidence_pack": json.loads(pack_to_json(pack))},
        indent=0,
    )
    try:
        data, _usage, model = call_openai_json(CHAT_SYSTEM, user, temperature=0.2)
        answer_text = str(data.get("answer") or "")
        if not answer_text.strip():
            raise ValueError("empty answer")
        return {
            "answer": answer_text,
            "follow_up_questions": data.get("follow_up_questions") or [],
            "cited_finding_ids": data.get("cited_finding_ids") or [],
            "confidence": data.get("confidence") or "medium",
            "source": "ai",
            "model": model,
            "report_id": str(report.id),
            "narration_available": True,
        }
    except Exception as e:
        logger.warning("chat_failed error=%s", e)
        result = _deterministic_answer(pack, question)
        result["report_id"] = str(report.id)
        result["source"] = "deterministic_fallback"
        result["narration_available"] = True
        return result
