"""Column mapping and bucket AR ingest tests."""

from pathlib import Path
from uuid import uuid4

import pandas as pd
import pytest
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Invoice, Organization
from app.services.digest import build_data_digest
from app.services.etl.aliases import normalize_columns
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


def test_customer_total_maps_to_amount_not_customer_name():
    cols = ["Customer", "Customer Total", "Current", "1-30", "Over 90"]
    mapping = normalize_columns(cols)
    assert mapping.get("Customer") == "customer_name"
    assert mapping.get("Customer Total") == "amount"
    assert "Current" not in mapping


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
