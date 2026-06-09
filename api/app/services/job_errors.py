"""Structured ingest job errors — user-facing message + operator detail."""

from __future__ import annotations

import traceback
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class JobError:
    code: str
    message: str
    hint: str | None = None
    detail: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        out = asdict(self)
        return {k: v for k, v in out.items() if v is not None}


def _ext(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def from_exception(exc: Exception, *, filename: str = "") -> JobError:
    ext = _ext(filename)
    raw = str(exc).strip() or exc.__class__.__name__
    detail = f"{exc.__class__.__name__}: {raw}"

    if isinstance(exc, ValueError) and raw.startswith("Unsupported file type"):
        return JobError(
            code="unsupported_format",
            message="This file type is not supported.",
            hint="Upload a CSV (.csv) or Excel (.xlsx) export from your ERP.",
            detail=detail,
        )

    if ext == "xls":
        return JobError(
            code="legacy_excel",
            message="Legacy Excel (.xls) files are not supported.",
            hint="Re-export from your ERP as CSV (.csv) or modern Excel (.xlsx).",
            detail=detail,
        )

    excel_markers = (
        "openpyxl",
        "BadZipFile",
        "Excel",
        "xlsx",
        "zip file",
        "Workbook",
    )
    if ext in ("xlsx", "xls") or any(m.lower() in raw.lower() for m in excel_markers):
        hint = (
            "Try exporting from your ERP as CSV (.csv) instead. "
            "If you need Excel, save as .xlsx (not .xls) with no password."
        )
        if "BadZipFile" in raw or "zip" in raw.lower():
            message = "This file looks like a CSV or text file saved with an .xlsx extension."
            hint = "Re-export as CSV (.csv) or save a real Excel workbook (.xlsx) from your ERP."
        elif "password" in raw.lower() or "encrypted" in raw.lower():
            message = "This Excel file appears to be password-protected."
            hint = "Remove the password in your ERP export settings, or export as CSV (.csv)."
        else:
            message = "We couldn't read this Excel file."
        return JobError(
            code="excel_read_failed",
            message=message,
            hint=hint,
            detail=detail,
        )

    if "codec" in raw.lower() or "decode" in raw.lower() or "encoding" in raw.lower():
        return JobError(
            code="encoding_failed",
            message="We couldn't read the text encoding in this file.",
            hint="Re-export as UTF-8 CSV from your ERP, or try saving as .xlsx.",
            detail=detail,
        )

    return JobError(
        code="processing_failed",
        message="Something went wrong while processing this file.",
        hint="Try re-exporting from your ERP as CSV (.csv). If the problem continues, contact support with the reference ID below.",
        detail=detail,
    )


def unknown_report_type(*, filename: str, columns: list[str]) -> JobError:
    ext = _ext(filename)
    col_preview = ", ".join(columns[:8]) if columns else "(no columns detected)"
    if len(columns) > 8:
        col_preview += ", …"

    if not columns:
        message = "The file appears empty or has no recognizable column headers."
        hint = (
            "Make sure you exported a data report (AR aging, AP aging, GL detail, or inventory) "
            "with column headers in the first few rows. CSV usually works best."
        )
    else:
        message = "We couldn't match this export to a known report type (AR aging, AP aging, GL, or inventory)."
        hint = (
            "Check that you uploaded the right export for the selected sector. "
            "Try CSV if Excel isn't working, and confirm column names like Customer, Vendor, Amount, or Invoice."
        )

    detail_parts = [f"extension=.{ext or 'unknown'}", f"columns=[{col_preview}]"]
    return JobError(
        code="unknown_report_type",
        message=message,
        hint=hint,
        detail="; ".join(detail_parts),
    )


def sector_disabled(sector: str) -> JobError:
    return JobError(
        code="sector_disabled",
        message=f"The {sector} sector is not available yet.",
        hint="Upload financials (AR/AP/GL) or manufacturing (inventory) exports instead.",
        detail=f"sector={sector}",
    )


def org_not_found() -> JobError:
    return JobError(
        code="org_not_found",
        message="Your workspace could not be found.",
        hint="Refresh the page or sign out and back in. Contact support if this persists.",
        detail="organization record missing",
    )


def normalize_stored_error(item: Any, *, include_detail: bool = False) -> dict[str, str | None]:
    if isinstance(item, dict):
        out = {
            "code": str(item.get("code") or "processing_failed"),
            "message": str(item.get("message") or item.get("detail") or "Processing failed"),
            "hint": item.get("hint"),
            "detail": item.get("detail") if include_detail else None,
        }
        return out
    text = str(item).strip() if item is not None else ""
    if not text:
        return {
            "code": "processing_failed",
            "message": "Processing failed",
            "hint": None,
            "detail": None,
        }
    return {
        "code": "legacy",
        "message": _legacy_user_message(text),
        "hint": _legacy_hint(text),
        "detail": text if include_detail else None,
    }


def _legacy_user_message(text: str) -> str:
    lower = text.lower()
    if "could not detect report type" in lower:
        return "We couldn't match this export to a known report type."
    if "unsupported file type" in lower:
        return "This file type is not supported."
    if "not enabled" in lower:
        return text
    return text.split("\n", 1)[0][:280]


def _legacy_hint(text: str) -> str | None:
    lower = text.lower()
    if "could not detect" in lower or "parse file" in lower:
        return "Try exporting as CSV (.csv) from your ERP with column headers intact."
    if "unsupported file" in lower:
        return "Upload CSV (.csv) or Excel (.xlsx) only."
    return None


def format_traceback(exc: BaseException) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).strip()


def scrub_detail_for_log(detail: str | None, max_len: int = 2000) -> str | None:
    if not detail:
        return None
    return detail[:max_len]
