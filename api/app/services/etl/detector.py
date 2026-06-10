"""Detect report type from filename, column headers, and upload sector hint."""

from __future__ import annotations

from app.services.etl.classifier import classify_dataset


def detect_report_type(
    filename: str,
    columns: list[str],
    sector_hint: str | None = None,
) -> str:
    classification = classify_dataset(filename, columns, profiles=[], sector_hint=sector_hint)
    likely = classification.likely_type
    if likely == "unknown_operational_export":
        return "unknown"
    return likely
