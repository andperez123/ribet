"""Tests for structured ingest job errors."""

from app.services.job_errors import (
    from_exception,
    normalize_stored_error,
    unknown_report_type,
)


def test_from_exception_legacy_xls():
    err = from_exception(
        ValueError("Legacy .xls workbooks require a separate reader"),
        filename="report.xls",
    )
    assert err.code == "legacy_excel"
    assert "Legacy Excel" in err.message
    assert err.hint and "CSV" in err.hint


def test_from_exception_bad_zip_xlsx():
    err = from_exception(
        ValueError("Excel read failed: File is not a zip file"),
        filename="export.xlsx",
    )
    assert err.code == "excel_read_failed"
    assert "CSV" in (err.hint or "")


def test_unknown_report_type_includes_columns():
    err = unknown_report_type(
        filename="data.xlsx",
        columns=["Col A", "Col B", "Amount"],
    )
    assert err.code == "unknown_report_type"
    assert "A" in (err.detail or "")
    assert err.hint and "CSV" in err.hint


def test_normalize_legacy_string_error():
    out = normalize_stored_error("Could not detect report type or parse file")
    assert out["code"] == "legacy"
    assert "report type" in out["message"].lower()
    assert out["hint"]


def test_normalize_structured_error():
    out = normalize_stored_error(
        {
            "code": "excel_read_failed",
            "message": "We couldn't read this Excel file.",
            "hint": "Try CSV.",
            "detail": "BadZipFile: not a zip",
        },
        include_detail=True,
    )
    assert out["code"] == "excel_read_failed"
    assert out["message"] == "We couldn't read this Excel file."
    assert out["detail"] == "BadZipFile: not a zip"


def test_normalize_strips_detail_for_clients():
    out = normalize_stored_error(
        {
            "code": "processing_failed",
            "message": "Something went wrong.",
            "detail": "Traceback (most recent call last): ...",
        }
    )
    assert out["detail"] is None
