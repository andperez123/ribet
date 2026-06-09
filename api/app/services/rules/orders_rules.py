"""Transactional rules for purchase orders and sales orders."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import PurchaseOrder, SalesOrder
from app.services.analysis_context import AnalysisContext
from app.services.rules.types import RuleFinding, RuleScope

LATE_PO_DAYS = 7
LATE_PO_TOTAL_THRESHOLD = 10_000.0
PAST_DUE_SO_DAYS = 1


def _po_query(db: Session, org_id, scope: RuleScope | None = None):
    q = db.query(PurchaseOrder).filter(PurchaseOrder.org_id == org_id)
    if scope:
        if scope.period:
            q = q.filter(PurchaseOrder.period_label == scope.period)
        if scope.source_job_ids:
            q = q.filter(PurchaseOrder.source_job_id.in_(scope.source_job_ids))
    return q


def _so_query(db: Session, org_id, scope: RuleScope | None = None):
    q = db.query(SalesOrder).filter(SalesOrder.org_id == org_id)
    if scope:
        if scope.period:
            q = q.filter(SalesOrder.period_label == scope.period)
        if scope.source_job_ids:
            q = q.filter(SalesOrder.source_job_id.in_(scope.source_job_ids))
    return q


def run_orders_rules(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    if ctx.includes("orders"):
        findings.extend(_check_late_purchase_orders(db, ctx))
    if ctx.includes("sales"):
        findings.extend(_check_past_due_sales_orders(db, ctx))
    return findings


def _check_late_purchase_orders(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    scope = ctx.scope
    rows = (
        _po_query(db, ctx.org_id, scope)
        .filter(PurchaseOrder.days_late >= LATE_PO_DAYS, PurchaseOrder.open_amount > 0)
        .order_by(PurchaseOrder.open_amount.desc())
        .all()
    )
    if not rows:
        return []

    total_late = float(sum(r.open_amount or 0 for r in rows))
    top = rows[0]
    vendor = top.vendor_name or top.vendor_id
    po_id = top.po_id
    days = top.days_late or 0
    open_amt = float(top.open_amount or 0)

    findings: list[RuleFinding] = [
        RuleFinding(
            finding_type="po_vendor_late",
            title=f"Expedite PO {po_id} — {vendor} is {days} days late",
            detail=(
                f"Purchase order {po_id} from {vendor} is {days} days past promise date "
                f"with ${open_amt:,.0f} still open"
                + (f" on SKU {top.sku}." if top.sku else ".")
            ),
            severity="high" if days >= 14 or open_amt >= 25_000 else "medium",
            confidence=0.94,
            business_impact="operations",
            department="procurement",
            category="fulfillment",
            suggested_action=(
                f"Contact {vendor} today to expedite PO {po_id}; confirm receipt date "
                f"and update buyers on any dependent production or sales orders."
            ),
            evidence={
                "po_id": po_id,
                "vendor_name": vendor,
                "days_late": days,
                "open_amount": open_amt,
                "sku": top.sku,
            },
        )
    ]

    if total_late >= LATE_PO_TOTAL_THRESHOLD or len(rows) >= 3:
        findings.append(
            RuleFinding(
                finding_type="po_late_cluster",
                title="Multiple late purchase orders blocking supply",
                detail=(
                    f"{len(rows)} open PO line(s) are at least {LATE_PO_DAYS} days late, "
                    f"totaling ${total_late:,.0f} in open value."
                ),
                severity="high" if total_late >= 50_000 else "medium",
                confidence=0.9,
                business_impact="operations",
                department="procurement",
                category="fulfillment",
                suggested_action=(
                    "Hold a vendor expedite review this week — prioritize the top three late POs "
                    "by open dollar value and assign a buyer owner for each."
                ),
                evidence={
                    "late_po_count": len(rows),
                    "late_po_total": total_late,
                    "top_po_id": po_id,
                },
            )
        )

    return findings


def _check_past_due_sales_orders(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    scope = ctx.scope
    rows = (
        _so_query(db, ctx.org_id, scope)
        .filter(SalesOrder.days_late >= PAST_DUE_SO_DAYS, SalesOrder.open_amount > 0)
        .order_by(SalesOrder.open_amount.desc())
        .all()
    )
    if not rows:
        return []

    total_at_risk = float(sum(r.open_amount or 0 for r in rows))
    top = rows[0]
    customer = top.customer_name or top.customer_id
    order_id = top.order_id
    days = top.days_late or 0
    open_amt = float(top.open_amount or 0)

    findings: list[RuleFinding] = [
        RuleFinding(
            finding_type="so_past_due_ship",
            title=f"Sales order {order_id} is {days} days past due — ${open_amt:,.0f} at risk",
            detail=(
                f"Customer {customer} has open order {order_id} "
                f"{days} day(s) past the ship/promise date with ${open_amt:,.0f} still open"
                + (f" on SKU {top.sku}." if top.sku else ".")
            ),
            severity="high" if days >= 7 or open_amt >= 25_000 else "medium",
            confidence=0.93,
            business_impact="revenue",
            department="operations",
            category="fulfillment",
            suggested_action=(
                f"Review production and procurement status for SO {order_id}; "
                f"confirm ship date with the customer and escalate any blocking POs."
            ),
            evidence={
                "order_id": order_id,
                "customer_name": customer,
                "days_late": days,
                "open_amount": open_amt,
                "sku": top.sku,
            },
        )
    ]

    if total_at_risk >= 25_000 or len(rows) >= 5:
        findings.append(
            RuleFinding(
                finding_type="so_backlog_at_risk",
                title="Past-due sales backlog threatens revenue",
                detail=(
                    f"{len(rows)} sales order line(s) are past due to ship, "
                    f"totaling ${total_at_risk:,.0f} in open revenue."
                ),
                severity="high" if total_at_risk >= 100_000 else "medium",
                confidence=0.88,
                business_impact="revenue",
                department="operations",
                category="fulfillment",
                suggested_action=(
                    "Run a daily ship-risk standup until backlog clears — rank orders by "
                    "open dollar value and customer priority."
                ),
                evidence={
                    "past_due_so_count": len(rows),
                    "past_due_so_total": total_at_risk,
                    "top_order_id": order_id,
                },
            )
        )

    return findings
