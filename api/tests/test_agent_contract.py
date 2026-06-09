"""Tests for agent contract builders."""

from uuid import uuid4

from app.services.agent_contract import (
    build_agent_roster,
    build_blocked_analyses,
    enrich_top_signals,
    split_unlocks,
)
from app.services.ai_analyst.runner import AnalystResult
from app.services.digest import DataDigest


def test_build_agent_roster_controller_complete():
    digest = DataDigest()
    digest.ar_total = 100_000
    digest.ar_invoice_count = 10
    coverage = {"ar": True, "ap": False, "gl": False, "inventory": False}
    roster = build_agent_roster(coverage, [], None, digest)
    controller = next(r for r in roster if r["agent"] == "controller")
    assert controller["status"] == "complete"
    assert controller["evidence_pack_version"] is not None


def test_build_agent_roster_locked_procurement():
    digest = DataDigest()
    coverage = {"ar": True, "ap": False, "gl": False, "inventory": False}
    roster = build_agent_roster(coverage, [], None, digest)
    procurement = next(r for r in roster if r["agent"] == "procurement")
    assert procurement["status"] == "locked"


def test_enrich_top_signals_includes_finding_id():
    from app.services.rules.types import RuleFinding

    finding = RuleFinding(
        finding_type="ar_aging_spike",
        title="AR spike",
        detail="Detail",
        severity="high",
        confidence=0.9,
        business_impact="Cash risk",
        department="finance",
        category="financial",
        suggested_action="Review AR",
        finding_id="F-AR-001",
    )
    trace = {"upload_label": "AR Aging", "period": "2026-06", "row_count": 96}
    signals = enrich_top_signals(
        [{"kind": "finding", "title": "AR spike", "body": "Detail", "severity": "high"}],
        [finding],
        trace,
        True,
    )
    assert signals[0]["finding_id"] == "F-AR-001"
    assert signals[0]["why_it_matters"] == "Cash risk"
    assert "agent" not in signals[0]


def test_split_unlocks():
    result = split_unlocks(
        [{"type": "confidence_increase", "message": "Confidence up"}],
        [{"analysis_name": "Inventory vs Demand", "requires_uploads": ["Open Sales Orders"]}],
        1,
    )
    assert len(result["unlocked"]) == 1
    assert len(result["still_gated"]) >= 1
