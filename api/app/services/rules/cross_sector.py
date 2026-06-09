from __future__ import annotations

"""Cross-sector deterministic rules."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import PurchaseOrder, SalesOrder
from app.services.analysis_context import AnalysisContext
from app.services.rules.finding_registry import enrich_findings
from app.services.rules.types import RuleFinding


def run_cross_sector_rules(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    if ctx.op_snap is None or ctx.coverage is None:
        return []

    findings: list[RuleFinding] = []
    findings.extend(_ar_inventory_cash_pressure(ctx, ctx.findings))
    findings.extend(_ar_ap_working_capital(ctx, ctx.findings))
    findings.extend(_gl_inventory_writeoff(ctx, ctx.findings))
    findings.extend(_po_so_fulfillment_gap(db, ctx))
    return enrich_findings(findings, ctx.period, ctx.org_id)


def _ar_inventory_cash_pressure(
    ctx: AnalysisContext,
    existing_findings: list[RuleFinding],
) -> list[RuleFinding]:
    coverage = ctx.coverage
    op_snap = ctx.op_snap
    assert coverage is not None and op_snap is not None

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
            evidence={
                "ar_over_90_pct": op_snap.ar_over_90_pct,
                "inventory_value": op_snap.inventory_value,
            },
        )
    ]


def _ar_ap_working_capital(
    ctx: AnalysisContext,
    existing_findings: list[RuleFinding],
) -> list[RuleFinding]:
    coverage = ctx.coverage
    op_snap = ctx.op_snap
    assert coverage is not None and op_snap is not None

    if not coverage.has("ar_aging") or not coverage.has("ap_aging"):
        return []

    ar_pct = op_snap.ar_over_90_pct or 0
    vendor_conc = op_snap.vendor_concentration or 0
    ar_elevated = ar_pct >= 15 or any(
        f.finding_type == "ar_aging_spike" for f in existing_findings
    )
    ap_elevated = vendor_conc >= 30 or any(
        f.finding_type == "vendor_concentration" for f in existing_findings
    )

    if not (ar_elevated or ap_elevated):
        return []

    detail = (
        f"AR over 90 is {ar_pct:.1f}% of receivables; "
        f"top vendor concentration is {vendor_conc:.1f}% of open AP. "
        "With both AR and AP data present, monitor net working capital and "
        "whether collections are keeping pace with payables."
    )

    return [
        RuleFinding(
            finding_type="ar_ap_working_capital",
            title="Receivables and payables both warrant attention",
            detail=detail,
            severity="high" if ar_elevated and ap_elevated else "medium",
            confidence=0.85,
            business_impact="cash_flow",
            department="finance",
            category="financial",
            suggested_action=(
                "Compare DSO vs DPO trends and prioritize collections on aged AR "
                "while reviewing concentrated vendor payables."
            ),
            evidence={"ar_over_90_pct": ar_pct, "vendor_concentration_pct": vendor_conc},
        )
    ]


def _gl_inventory_writeoff(
    ctx: AnalysisContext,
    existing_findings: list[RuleFinding],
) -> list[RuleFinding]:
    coverage = ctx.coverage
    assert coverage is not None

    if not coverage.has("gl_detail") or not coverage.has("inventory"):
        return []

    has_gl_signal = any(
        f.finding_type in ("missing_gl_mappings", "inventory_adjustment_spike")
        for f in existing_findings
    )
    has_inv_signal = any(
        f.finding_type
        in ("inventory_adjustment_spike", "orphan_inventory", "negative_inventory")
        for f in existing_findings
    )

    if not (has_gl_signal and has_inv_signal):
        return []

    return [
        RuleFinding(
            finding_type="gl_inventory_writeoff_pattern",
            title="GL adjustments coincide with inventory integrity issues",
            detail=(
                "General ledger adjustment activity and inventory mapping or quantity "
                "issues appear together. This pattern may indicate write-offs, shrinkage, "
                "or costing adjustments that need controller review."
            ),
            severity="medium",
            confidence=0.82,
            business_impact="margin",
            department="finance",
            category="operational",
            suggested_action=(
                "Reconcile GL adjustment accounts against recent inventory adjustments "
                "and verify SKU costing."
            ),
            evidence={"gl_and_inventory_signals": True},
        )
    ]


def _po_so_fulfillment_gap(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    coverage = ctx.coverage
    assert coverage is not None

    if not coverage.has("purchase_orders") or not coverage.has("sales_orders"):
        return []

    period = ctx.period
    po_q = db.query(PurchaseOrder).filter(
        PurchaseOrder.org_id == ctx.org_id,
        PurchaseOrder.days_late >= 7,
        PurchaseOrder.open_amount > 0,
    )
    so_q = db.query(SalesOrder).filter(
        SalesOrder.org_id == ctx.org_id,
        SalesOrder.days_late >= 1,
        SalesOrder.open_amount > 0,
    )
    if period:
        po_q = po_q.filter(PurchaseOrder.period_label == period)
        so_q = so_q.filter(SalesOrder.period_label == period)

    late_po_total = float(po_q.with_entities(func.sum(PurchaseOrder.open_amount)).scalar() or 0)
    past_due_so_total = float(so_q.with_entities(func.sum(SalesOrder.open_amount)).scalar() or 0)
    if late_po_total <= 0 or past_due_so_total <= 0:
        return []

    top_po = po_q.order_by(PurchaseOrder.open_amount.desc()).first()
    vendor = (top_po.vendor_name or top_po.vendor_id) if top_po else "key vendor"
    po_id = top_po.po_id if top_po else "top PO"

    return [
        RuleFinding(
            finding_type="po_so_fulfillment_gap",
            title="Late POs may be blocking past-due sales orders",
            detail=(
                f"${late_po_total:,.0f} in purchase orders are late while "
                f"${past_due_so_total:,.0f} in sales orders are past due to ship. "
                f"Expediting {vendor} (PO {po_id}) may unblock customer shipments."
            ),
            severity="high" if past_due_so_total >= 50_000 else "medium",
            confidence=0.86,
            business_impact="revenue",
            department="operations",
            category="fulfillment",
            suggested_action=(
                f"Expedite PO {po_id} with {vendor} this week and re-promise ship dates "
                "on the largest past-due sales orders."
            ),
            evidence={
                "late_po_total": late_po_total,
                "past_due_so_total": past_due_so_total,
                "po_id": po_id,
                "vendor_name": vendor,
            },
        )
    ]
