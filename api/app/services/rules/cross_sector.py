from __future__ import annotations

"""Cross-sector deterministic rules (AR + inventory → operational cash pressure)."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import OperationalSnapshot
from app.services.graph.coverage import get_graph_coverage
from app.services.rules.runner import RuleFinding


def run_cross_sector_rules(
    db: Session,
    org_id: UUID,
    op_snap: OperationalSnapshot | None,
    existing_findings: list[RuleFinding],
) -> list[RuleFinding]:
    if op_snap is None:
        return []

    coverage = get_graph_coverage(db, org_id)
    if not coverage.has("ar_aging") or not coverage.has("inventory"):
        return []

    ar_elevated = (op_snap.ar_over_90_pct or 0) >= 15
    has_ar_finding = any(f.finding_type == "ar_aging_spike" for f in existing_findings)
    inventory_present = (op_snap.inventory_value or 0) > 0
    has_inventory_signal = any(
        f.finding_type in ("inventory_adjustment_spike", "orphan_inventory")
        for f in existing_findings
    )

    if not ((ar_elevated or has_ar_finding) and inventory_present):
        return []

    detail_parts = []
    if op_snap.ar_over_90_pct is not None:
        detail_parts.append(f"AR over 90 is {op_snap.ar_over_90_pct:.1f}% of receivables")
    if op_snap.inventory_value is not None:
        detail_parts.append(f"inventory on hand totals {op_snap.inventory_value:,.0f} units")
    if has_inventory_signal:
        detail_parts.append("inventory adjustment or mapping issues detected")

    detail = "; ".join(detail_parts) + ". "
    detail += (
        "Together this may indicate cash trapped in receivables and inventory. "
        "Upload AP Aging, Open Sales Orders, and Purchase Orders to diagnose further."
    )

    return [
        RuleFinding(
            finding_type="operational_cash_pressure",
            title="AR and inventory signals both elevated",
            detail=detail,
            severity="high" if ar_elevated and has_inventory_signal else "medium",
            confidence=0.88,
            business_impact="cash_flow",
            department="finance",
            category="risk",
            suggested_action=(
                "Upload AP Aging, Open Sales Orders, and Purchase Orders "
                "to determine whether cash is trapped in operations."
            ),
        )
    ]
