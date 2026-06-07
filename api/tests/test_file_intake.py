"""File intake tests — preamble, delimiter, header detection."""

from pathlib import Path

import pytest

from app.services.etl.file_intake import intake_csv, intake_file
from app.services.etl.detector import detect_report_type
from app.services.transforms.adapters.generic import dataframe_to_canonical

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def test_preamble_csv_skips_title_rows():
    content = (FIXTURES / "ar_aging_with_preamble.csv").read_bytes()
    result = intake_csv(content)
    assert result.metadata.skipped_rows >= 3
    assert "Customer" in result.dataframe.columns
    assert len(result.dataframe) == 3
    report_type = detect_report_type("ar.csv", list(result.dataframe.columns))
    assert report_type == "ar_aging"


def test_semicolon_delimiter():
    content = (FIXTURES / "ar_aging_semicolon.csv").read_bytes()
    result = intake_csv(content)
    assert result.metadata.delimiter == ";"
    assert "Customer" in result.dataframe.columns
    assert len(result.dataframe) == 2


def test_intake_produces_canonical_rows():
    content = (FIXTURES / "ar_aging_with_preamble.csv").read_bytes()
    result = intake_file(content, "ar.csv")
    dataset = dataframe_to_canonical("ar_aging", result.dataframe)
    assert len(dataset.ar) == 3
    assert all(r.amount > 0 for r in dataset.ar)
