"""Tests for unified AnalysisContext rule signatures and finding IDs."""

from __future__ import annotations

import inspect
from uuid import uuid4

import pytest

from app.services.analysis_context import AnalysisContext
from app.services.rules import cross_sector, runner
from app.services.rules.finding_registry import FINDING_REGISTRY, enrich_finding
from app.services.rules.types import RuleFinding


def _all_domain_rules():
    names = [
        name
        for name, fn in inspect.getmembers(runner, inspect.isfunction)
        if name.startswith("_check_") and name != "_check_snapshot_deltas"
    ]
    return names


def test_domain_rules_accept_db_and_ctx():
    for name in _all_domain_rules():
        fn = getattr(runner, name)
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        assert params == ["db", "ctx"], f"{name} must use (db, ctx) signature, got {params}"


def test_cross_sector_rules_accept_db_and_ctx():
    sig = inspect.signature(cross_sector.run_cross_sector_rules)
    assert list(sig.parameters.keys()) == ["db", "ctx"]


def test_snapshot_delta_rules_accept_db_and_ctx():
    sig = inspect.signature(runner.run_snapshot_delta_rules)
    assert list(sig.parameters.keys()) == ["db", "ctx"]


def test_finding_id_stable_by_rule_type():
    finding = RuleFinding(
        finding_type="customer_concentration",
        title="Customer concentration risk",
        detail="test",
        severity="high",
        confidence=0.9,
        business_impact="cash_flow",
        department="finance",
        category="risk",
        suggested_action="Review",
    )
    enrich_finding(finding, "2026-06", uuid4())
    assert finding.finding_id == "F-AR-001"
    assert finding.source_metric_keys == list(FINDING_REGISTRY["customer_concentration"].source_metric_keys)


def test_finding_instance_id_unique_per_fingerprint():
    base = dict(
        finding_type="customer_concentration",
        detail="test",
        severity="high",
        confidence=0.9,
        business_impact="cash_flow",
        department="finance",
        category="risk",
        suggested_action="Review",
    )
    f1 = RuleFinding(title="Customer A risk", **base)
    f2 = RuleFinding(title="Customer B risk", **base)
    enrich_finding(f1, "2026-06", uuid4())
    enrich_finding(f2, "2026-06", uuid4())
    assert f1.finding_id == f2.finding_id == "F-AR-001"
    assert f1.finding_instance_id != f2.finding_instance_id


def test_cross_sector_gl_inventory_writeoff_fires_on_adjustment_spike(db_session, sample_org):
    from app.models import OperationalSnapshot
    from app.services.graph.coverage import CoverageItem, GraphCoverage
    from app.services.rules.cross_sector import run_cross_sector_rules

    ctx = AnalysisContext(
        org_id=sample_org.id,
        period="2026-06",
        source_job_ids=None,
        domains={"gl", "inventory"},
    )
    ctx.op_snap = OperationalSnapshot(
        org_id=sample_org.id,
        period="2026-06",
        health_score=90,
        health_status="Stable",
    )
    ctx.coverage = GraphCoverage(
        items=[
            CoverageItem(
                key="gl_detail", label="GL", sector="financials", covered=True, uploadable=True
            ),
            CoverageItem(
                key="inventory", label="Inventory", sector="manufacturing", covered=True, uploadable=True
            ),
        ],
    )
    ctx.findings = [
        RuleFinding(
            finding_type="inventory_adjustment_spike",
            title="Inventory adjustments above baseline",
            detail="test",
            severity="high",
            confidence=0.88,
            business_impact="margin",
            department="operations",
            category="operational",
            suggested_action="Review",
        ),
        RuleFinding(
            finding_type="orphan_inventory",
            title="Orphan inventory items",
            detail="test",
            severity="medium",
            confidence=1.0,
            business_impact="inventory",
            department="operations",
            category="data_quality",
            suggested_action="Map GL",
        ),
    ]
    results = run_cross_sector_rules(db_session, ctx)
    types = {f.finding_type for f in results}
    assert "gl_inventory_writeoff_pattern" in types


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
    from app.models import Organization

    org = Organization(id=uuid4(), name="Test Org", erp_family="jobboss")
    db_session.add(org)
    db_session.commit()
    return org
