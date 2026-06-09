"""Tests for purchase order and sales order ingest + transactional rules."""

from __future__ import annotations

from datetime import date, timedelta
from io import StringIO
from uuid import uuid4

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Organization, PurchaseOrder, SalesOrder
from app.services.analysis_context import AnalysisContext
from app.services.digest import build_data_digest
from app.services.etl.detector import detect_report_type
from app.services.etl.field_mapper import propose_mapping
from app.services.etl.profiler import profile_dataframe
from app.services.rules.orders_rules import run_orders_rules
from app.services.transforms.adapters import generic as generic_adapter
from app.services.transforms.persist import persist_canonical


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    org = Organization(id=uuid4(), name="Test Mfg", erp_family="generic")
    session.add(org)
    session.commit()
    yield session, org
    session.close()


def test_detect_purchase_orders_from_columns():
    cols = ["PO Number", "Vendor Name", "Promise Date", "Open Amount", "Status"]
    assert detect_report_type("export.csv", cols, sector_hint="orders") == "purchase_orders"


def test_purchase_order_adapter_and_rules(db):
    session, org = db
    late_date = (date.today() - timedelta(days=14)).isoformat()
    csv = (
        "PO Number,Vendor Name,Promise Date,Open Amount,Status,SKU\n"
        f"PO-123,Acme Supply,{late_date},25000,Open,BRG-100\n"
        f"PO-456,Beta Parts,{late_date},5000,Open,WID-22\n"
    )
    df = pd.read_csv(StringIO(csv))
    profiles = profile_dataframe(df)
    plan = propose_mapping(profiles, "purchase_orders", list(df.columns))
    dataset = generic_adapter.dataframe_to_canonical("purchase_orders", df, plan=plan)
    assert len(dataset.purchase_orders) == 2
    assert dataset.purchase_orders[0].po_id == "PO-123"
    assert dataset.purchase_orders[0].days_late >= 14

    job_id = uuid4()
    row_count = persist_canonical(session, org.id, job_id, "2026-06", dataset)
    session.commit()
    assert row_count == 2

    digest = build_data_digest(session, org.id, period="2026-06", domains={"orders"})
    assert digest.po_count == 2
    assert digest.po_late_count == 2
    assert digest.po_late_total == 30000

    ctx = AnalysisContext(
        org_id=org.id,
        period="2026-06",
        source_job_ids=[job_id],
        domains={"orders"},
    )
    findings = run_orders_rules(session, ctx)
    assert any(f.finding_type == "po_vendor_late" for f in findings)
    expedite = next(f for f in findings if f.finding_type == "po_vendor_late")
    assert "PO-123" in expedite.title
    assert "Acme Supply" in expedite.detail
    assert "$25,000" in expedite.detail or "25000" in expedite.detail.replace(",", "")


def test_sales_order_past_due_rule(db):
    session, org = db
    late_ship = (date.today() - timedelta(days=5)).isoformat()
    csv = (
        "Sales Order,Customer Name,Ship Date,Open Amount,Status\n"
        f"SO-9001,Big Customer Inc,{late_ship},75000,Open\n"
    )
    df = pd.read_csv(StringIO(csv))
    profiles = profile_dataframe(df)
    plan = propose_mapping(profiles, "sales_orders", list(df.columns))
    dataset = generic_adapter.dataframe_to_canonical("sales_orders", df, plan=plan)
    assert len(dataset.sales_orders) == 1

    job_id = uuid4()
    persist_canonical(session, org.id, job_id, "2026-06", dataset)
    session.commit()

    ctx = AnalysisContext(
        org_id=org.id,
        period="2026-06",
        source_job_ids=[job_id],
        domains={"sales"},
    )
    findings = run_orders_rules(session, ctx)
    assert any(f.finding_type == "so_past_due_ship" for f in findings)
    finding = next(f for f in findings if f.finding_type == "so_past_due_ship")
    assert "SO-9001" in finding.title
    assert "Big Customer Inc" in finding.detail
