"""Tests for Evidence Pack assembly and privacy constraints."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from app.models import Organization
from app.schemas.evidence_pack import EVIDENCE_PACK_SCHEMA_VERSION
from app.services.evidence_pack import build_evidence_pack
from app.services.report import generate_report


RAW_ROW_KEYS = {
    "invoice_id",
    "invoice_number",
    "customer_id",
    "transaction_id",
    "sku",
    "item_id",
    "gl_account",
    "posted_at",
}


def _collect_keys(obj, keys: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in RAW_ROW_KEYS:
                keys.add(k)
            _collect_keys(v, keys)
    elif isinstance(obj, list):
        for item in obj:
            _collect_keys(item, keys)


def test_evidence_pack_metrics_match_digest(db_session, sample_org):
    from app.models import Invoice, OperationalReport

    period = "2026-06"
    for i in range(5):
        db_session.add(
            Invoice(
                org_id=sample_org.id,
                invoice_id=f"INV-{i}",
                customer_id=f"CUST-{i}",
                amount=10000.0,
                days_overdue=0,
                period_label=period,
            )
        )
    db_session.commit()

    report = generate_report(db_session, sample_org.id, job_ids=[], period=period)
    from app.models import EvidencePackRecord

    row = (
        db_session.query(EvidencePackRecord)
        .filter(EvidencePackRecord.report_id == report.id)
        .first()
    )
    assert row is not None
    pack = build_evidence_pack(db_session, report.id, findings=None)

    assert row.pack["schema_version"] == EVIDENCE_PACK_SCHEMA_VERSION
    assert row.pack["agent_ready"] is True
    assert row.pack["raw_data_included"] is True
    assert pack.metrics["ar"]["total_receivables"] == pytest.approx(50000.0)
    assert report.data_digest["ar_total"] == pytest.approx(50000.0)
    assert row.pack["memory"]["enabled"] is False
    assert row.pack["memory"]["recurring_findings"] == []


def test_evidence_pack_findings_have_ids_and_metric_keys(db_session, sample_org):
    from app.models import Invoice

    period = "2026-06"
    amounts = [50000.0, 1000.0, 1000.0, 1000.0]
    for i, amount in enumerate(amounts):
        db_session.add(
            Invoice(
                org_id=sample_org.id,
                invoice_id=f"INV-{i}",
                customer_id=f"CUST-{i % 3}",
                amount=amount,
                days_overdue=0,
                period_label=period,
            )
        )
    db_session.commit()

    report = generate_report(db_session, sample_org.id, job_ids=[], period=period)
    from app.models import EvidencePackRecord

    row = (
        db_session.query(EvidencePackRecord)
        .filter(EvidencePackRecord.report_id == report.id)
        .first()
    )
    assert row is not None
    concentration = [f for f in row.pack["findings"] if f["finding_id"] == "F-AR-001"]
    assert concentration, "expected customer concentration finding"
    f = concentration[0]
    assert f["finding_instance_id"].startswith("F-AR-001-")
    assert f["source_metric_keys"]
    assert f["evidence"]


def test_evidence_pack_no_raw_row_level_data(db_session, sample_org):
    from app.models import Invoice

    period = "2026-06"
    db_session.add(
        Invoice(
            org_id=sample_org.id,
            invoice_id="INV-1",
            customer_id="C1",
            amount=5000.0,
            days_overdue=0,
            period_label=period,
        )
    )
    db_session.commit()

    report = generate_report(db_session, sample_org.id, job_ids=[], period=period)
    from app.models import EvidencePackRecord

    row = (
        db_session.query(EvidencePackRecord)
        .filter(EvidencePackRecord.report_id == report.id)
        .first()
    )
    assert row is not None

    raw_keys: set[str] = set()
    _collect_keys(row.pack, raw_keys)
    assert not raw_keys, f"Evidence pack must not contain raw row keys, found: {raw_keys}"

    serialized = json.dumps(row.pack)
    assert "invoice_id" not in serialized
    assert "INV-1" not in serialized


def test_analysis_boundaries_include_missing_sector_gaps(db_session, sample_org):
    from app.models import Invoice

    period = "2026-06"
    db_session.add(
        Invoice(
            org_id=sample_org.id,
            invoice_id="INV-1",
            customer_id="C1",
            amount=1000.0,
            days_overdue=0,
            period_label=period,
        )
    )
    db_session.commit()

    report = generate_report(db_session, sample_org.id, job_ids=[], period=period)
    from app.models import EvidencePackRecord

    row = (
        db_session.query(EvidencePackRecord)
        .filter(EvidencePackRecord.report_id == report.id)
        .first()
    )
    assert row is not None
    cannot = row.pack["analysis_boundaries"]["cannot_conclude"]
    assert any("sales orders" in c.lower() for c in cannot)


@pytest.fixture
def db_session():
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_org(db_session):
    org = Organization(id=uuid4(), name="Evidence Pack Test", erp_family="jobboss")
    db_session.add(org)
    db_session.commit()
    return org
