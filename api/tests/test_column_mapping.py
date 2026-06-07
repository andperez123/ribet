"""Column mapping and bucket AR/AP ingest tests."""

from pathlib import Path
from uuid import uuid4

import pandas as pd
import pytest
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Invoice, Organization, Vendor
from app.services.digest import build_data_coverage, build_data_digest, domains_for_report_type
from app.services.etl.aliases import detect_aging_bucket_columns, normalize_columns
from app.services.report_insights import hydrate_report_insights
from app.services.transforms.adapters.generic import dataframe_to_canonical
from app.services.transforms.persist import persist_canonical
from app.services.etl.detector import detect_report_type

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    org = Organization(id=uuid4(), name="Mapping Test Org", erp_family="generic")
    session.add(org)
    session.commit()
    yield session, org
    session.close()


def test_vendor_name_maps_to_vendor_not_customer():
    cols = ["Vendor ID", "Vendor Name", "Open Balance"]
    mapping = normalize_columns(cols)
    assert mapping.get("Vendor Name") == "vendor_name"
    assert mapping.get("Vendor ID") == "vendor_id"
    assert mapping.get("Open Balance") == "amount"


def test_customer_total_maps_to_amount_not_customer_name():
    cols = ["Customer", "Customer Total", "Current", "1-30", "Over 90"]
    mapping = normalize_columns(cols)
    assert mapping.get("Customer") == "customer_name"
    assert mapping.get("Customer Total") == "amount"
    assert "Current" not in mapping


def test_ap_user_format_headers_detect_buckets():
    cols = [
        "Vendor Name",
        "Total Owed ($)",
        "Current (0-30 Days)",
        "31-60 Days",
        "61-90 Days",
        "91+ Days",
    ]
    mapping = normalize_columns(cols)
    buckets = detect_aging_bucket_columns(cols)
    assert len(buckets) == 4
    assert mapping.get("Vendor Name") == "vendor_name"
    assert mapping.get("Total Owed ($)") == "amount"
    assert "31-60 Days" not in mapping
    assert "Current (0-30 Days)" not in mapping


def test_ap_user_format_ingest_with_bucket_breakdown(db):
    session, org = db
    df = pd.read_csv(FIXTURES / "ap_aging_user_format.csv")
    dataset = dataframe_to_canonical("ap_aging", df)
    assert len(dataset.ap) == 4
    assert sum(float(v.balance) for v in dataset.ap) == 56350
    bluescope = next(v for v in dataset.ap if "BlueScope" in (v.vendor_name or ""))
    assert bluescope.bucket_breakdown.get("31_60") == 26500
    assert bluescope.bucket_breakdown.get("current") == 15500

    job_id = uuid4()
    persist_canonical(session, org.id, job_id, "2026-06", dataset)
    session.commit()

    digest = build_data_digest(session, org.id, period="2026-06", source_job_ids=[job_id])
    assert digest.ap_total == 56350
    assert digest.ap_31_60 == 29800
    assert digest.ap_current == 26550
    coverage = build_data_coverage(digest, primary_domain="ap")
    assert coverage["ap"] is True
    assert coverage["ap_aging_available"] is True
    assert coverage["ar"] is False


def test_bucket_ar_aging_sums_amounts(db):
    session, org = db
    df = pd.read_csv(FIXTURES / "ar_aging_buckets.csv")
    report_type = detect_report_type("ar_aging_buckets.csv", list(df.columns))
    assert report_type == "ar_aging"

    dataset = dataframe_to_canonical(report_type, df)
    assert len(dataset.ar) == 6
    assert all(r.amount > 0 for r in dataset.ar)

    rows = persist_canonical(session, org.id, uuid4(), "2026-06", dataset)
    session.commit()
    assert rows > 0

    total = session.query(func.sum(Invoice.amount)).filter(Invoice.org_id == org.id).scalar()
    assert float(total or 0) > 100_000


def test_ar_user_format_ingest(db):
    session, org = db
    df = pd.read_csv(FIXTURES / "ar_aging_user_format.csv")
    dataset = dataframe_to_canonical("ar_aging", df)
    assert len(dataset.ar) == 6
    assert all(r.amount > 0 for r in dataset.ar)
    assert all(not str(r.customer_name or "").isdigit() for r in dataset.ar)


def test_mismapped_ar_filters_numeric_customers(db):
    session, org = db
    df = pd.read_csv(FIXTURES / "ar_aging_mismapped.csv")
    dataset = dataframe_to_canonical("ar_aging", df)
    assert len(dataset.ar) == 0


def test_coverage_ar_unmapped_without_dollar_kpis(db):
    session, org = db
    df = pd.read_csv(FIXTURES / "ar_aging_mismapped.csv")
    dataset = dataframe_to_canonical("ar_aging", df)
    if dataset.ar:
        persist_canonical(session, org.id, uuid4(), "2026-06", dataset)
        session.commit()

    bad_rows = [
        Invoice(
            org_id=org.id,
            invoice_id=f"inv-{i}",
            customer_id=str(14200 + i * 1000),
            amount=0,
            period_label="2026-06",
        )
        for i in range(6)
    ]
    for row in bad_rows:
        session.add(row)
    session.commit()

    digest = build_data_digest(session, org.id, period="2026-06")
    coverage = build_data_coverage(digest)
    assert coverage["ar"] is False
    assert coverage["ar_unmapped"] is True
    assert coverage["ar_present"] is True


def test_ap_report_scoping_excludes_stale_ar(db):
    session, org = db
    ar_job = uuid4()
    ap_job = uuid4()

    ar_df = pd.read_csv(FIXTURES / "ar_aging_mismapped.csv")
    for i in range(6):
        session.add(
            Invoice(
                org_id=org.id,
                invoice_id=f"bad-{i}",
                customer_id=str(14200 + i * 1000),
                amount=0,
                period_label="2026-06",
                source_job_id=ar_job,
            )
        )

    ap_df = pd.read_csv(FIXTURES / "ap_aging_user_format.csv")
    ap_dataset = dataframe_to_canonical("ap_aging", ap_df)
    persist_canonical(session, org.id, ap_job, "2026-06", ap_dataset)
    session.commit()

    all_digest = build_data_digest(session, org.id, period="2026-06")
    assert all_digest.ar_invoice_count == 6
    assert all_digest.ap_total == 56350

    scoped = build_data_digest(
        session,
        org.id,
        period="2026-06",
        source_job_ids=[ap_job],
        domains=domains_for_report_type("ap_aging"),
    )
    assert scoped.ar_invoice_count == 0
    assert scoped.ap_total == 56350


def test_customer_total_column_uses_buckets_when_present(db):
    session, org = db
    df = pd.read_csv(FIXTURES / "ar_aging_customer_total.csv")
    dataset = dataframe_to_canonical("ar_aging", df)
    assert len(dataset.ar) == 6
    assert all(r.amount > 0 for r in dataset.ar)
    assert all(not str(r.customer_name or "").startswith("$") for r in dataset.ar)

    persist_canonical(session, org.id, uuid4(), "2026-06", dataset)
    session.commit()

    digest = build_data_digest(session, org.id, period="2026-06")
    assert digest.ar_total > 0
    assert digest.ar_invoice_count == 6
    assert digest.top_customers
    assert digest.top_customers[0].amount > 0


def test_period_scoped_digest_isolates_periods(db):
    session, org = db
    df_june = pd.read_csv(FIXTURES / "ar_aging_buckets.csv")
    dataset_june = dataframe_to_canonical("ar_aging", df_june)
    persist_canonical(session, org.id, uuid4(), "2026-06", dataset_june)

    persist_canonical(session, org.id, uuid4(), "2026-05", dataset_june)
    session.commit()

    june_digest = build_data_digest(session, org.id, period="2026-06")
    may_digest = build_data_digest(session, org.id, period="2026-05")
    all_digest = build_data_digest(session, org.id)

    assert june_digest.ar_invoice_count == 6
    assert may_digest.ar_invoice_count == 6
    assert all_digest.ar_invoice_count == 12


def test_stale_frozen_digest_refreshes_on_read(db):
    from app.models import OperationalReport

    session, org = db
    df = pd.read_csv(FIXTURES / "ar_aging_buckets.csv")
    dataset = dataframe_to_canonical("ar_aging", df)
    persist_canonical(session, org.id, uuid4(), "2026-06", dataset)
    session.commit()

    report = OperationalReport(
        org_id=org.id,
        executive_summary=["Stale"],
        health_score=100,
        health_status="Stable",
        data_digest={
            "ar_total": 0,
            "ar_invoice_count": 6,
            "ar_over_90": 0,
            "ar_over_90_pct": 0,
            "top_customers": [],
            "ap_total": 0,
            "vendor_count": 0,
            "top_vendors": [],
            "gl_txn_count": 0,
            "gl_adjustment_total": 0,
            "gl_unmapped_count": 0,
            "inventory_item_count": 0,
            "inventory_total_qty": 0,
            "inventory_negative_count": 0,
            "inventory_zero_count": 0,
            "inventory_orphan_count": 0,
        },
        domain_insights=[],
        data_coverage={"ar": True, "ap": False, "gl": False, "inventory": False},
    )
    session.add(report)
    session.commit()

    bundle = hydrate_report_insights(session, report)
    assert bundle.hydrated is True
    assert bundle.analysis_metadata.get("insights_source") == "refreshed"
    assert bundle.data_digest["ar_total"] > 0
    assert len(bundle.domain_insights) > 0
