from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Customer, GlTransaction, InventoryItem, Invoice, Vendor
from app.services.analysis_context import AnalysisContext
from app.services.rules.finding_registry import enrich_findings
from app.services.rules.types import RuleFinding, RuleScope


def _invoice_query(db: Session, org_id: UUID, scope: RuleScope | None = None):
    q = db.query(Invoice).filter(Invoice.org_id == org_id)
    if scope:
        if scope.period:
            q = q.filter(Invoice.period_label == scope.period)
        if scope.source_job_ids:
            q = q.filter(Invoice.source_job_id.in_(scope.source_job_ids))
    return q


def _vendor_query(db: Session, org_id: UUID, scope: RuleScope | None = None):
    q = db.query(Vendor).filter(Vendor.org_id == org_id)
    if scope:
        if scope.period:
            q = q.filter(Vendor.period_label == scope.period)
        if scope.source_job_ids:
            q = q.filter(Vendor.source_job_id.in_(scope.source_job_ids))
    return q


def _gl_query(db: Session, org_id: UUID, scope: RuleScope | None = None):
    q = db.query(GlTransaction).filter(GlTransaction.org_id == org_id)
    if scope:
        if scope.period:
            q = q.filter(GlTransaction.period_label == scope.period)
        if scope.source_job_ids:
            q = q.filter(GlTransaction.source_job_id.in_(scope.source_job_ids))
    return q


def _inventory_query(db: Session, org_id: UUID, scope: RuleScope | None = None):
    q = db.query(InventoryItem).filter(InventoryItem.org_id == org_id)
    if scope:
        if scope.period:
            q = q.filter(InventoryItem.period_label == scope.period)
        if scope.source_job_ids:
            q = q.filter(InventoryItem.source_job_id.in_(scope.source_job_ids))
    return q


def run_rules(
    db: Session,
    org_id: UUID,
    *,
    period: str | None = None,
    source_job_ids: list[UUID] | None = None,
    domains: set[str] | None = None,
) -> list[RuleFinding]:
    ctx = AnalysisContext(
        org_id=org_id,
        period=period or "",
        source_job_ids=source_job_ids,
        domains=domains or set(),
    )
    findings: list[RuleFinding] = []
    if ctx.includes("ar"):
        findings.extend(_check_ar_zero_amounts(db, ctx))
        findings.extend(_check_ar_aging_spike(db, ctx))
        findings.extend(_check_customer_concentration(db, ctx))
        findings.extend(_check_duplicate_customers(db, ctx))
        findings.extend(_check_invalid_aging_buckets(db, ctx))
    if ctx.includes("ap"):
        findings.extend(_check_ap_negative(db, ctx))
        findings.extend(_check_vendor_concentration(db, ctx))
        findings.extend(_check_vendor_name_concentration(db, ctx))
        findings.extend(_check_duplicate_vendors(db, ctx))
    if ctx.includes("inventory"):
        findings.extend(_check_inventory_adjustments(db, ctx))
        findings.extend(_check_orphan_inventory(db, ctx))
        findings.extend(_check_negative_inventory(db, ctx))
        findings.extend(_check_zero_or_dead_stock_signals(db, ctx))
    if ctx.includes("gl"):
        findings.extend(_check_missing_gl_mappings(db, ctx))
    return enrich_findings(findings, ctx.period, ctx.org_id)


def run_snapshot_delta_rules(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    findings = _check_snapshot_deltas(db, ctx)
    return enrich_findings(findings, ctx.period, ctx.org_id)


def _normalize_name(name: str | None) -> str:
    return " ".join((name or "").lower().split())


def _check_snapshot_deltas(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    current = ctx.op_snap
    prior = ctx.prior_op_snap
    if not current or not prior:
        return []

    results: list[RuleFinding] = []
    if (
        current.ar_over_90_pct is not None
        and prior.ar_over_90_pct is not None
        and current.ar_over_90_pct - prior.ar_over_90_pct >= 5
    ):
        results.append(
            RuleFinding(
                finding_type="ar_aging_worsened",
                title="AR over 90 days increased vs prior period",
                detail=(
                    f"AR over 90 rose from {prior.ar_over_90_pct:.1f}% to "
                    f"{current.ar_over_90_pct:.1f}% of total receivables."
                ),
                severity="high",
                confidence=0.9,
                business_impact="cash_flow",
                department="finance",
                category="financial",
                suggested_action="Review collection workflow and top overdue accounts.",
                evidence={
                    "prior_pct": prior.ar_over_90_pct,
                    "current_pct": current.ar_over_90_pct,
                    "delta_pct": current.ar_over_90_pct - prior.ar_over_90_pct,
                },
            )
        )
    if (
        current.health_score
        and prior.health_score
        and prior.health_score - current.health_score >= 10
    ):
        results.append(
            RuleFinding(
                finding_type="health_score_declined",
                title="Operational health score declined",
                detail=f"Health score dropped from {prior.health_score} to {current.health_score}.",
                severity="medium",
                confidence=0.88,
                business_impact="cash_flow",
                department="finance",
                category="risk",
                suggested_action="Review latest findings and address high-severity items.",
                evidence={
                    "prior_score": prior.health_score,
                    "current_score": current.health_score,
                    "delta": prior.health_score - current.health_score,
                },
            )
        )
    if (
        current.vendor_concentration is not None
        and prior.vendor_concentration is not None
        and current.vendor_concentration - prior.vendor_concentration >= 10
    ):
        results.append(
            RuleFinding(
                finding_type="vendor_concentration_increased",
                title="Vendor concentration increased",
                detail=(
                    f"Top vendor AP share rose from {prior.vendor_concentration:.1f}% "
                    f"to {current.vendor_concentration:.1f}%."
                ),
                severity="medium",
                confidence=0.85,
                business_impact="cash_flow",
                department="purchasing",
                category="risk",
                suggested_action="Review vendor dependency and payment terms.",
                evidence={
                    "prior_pct": prior.vendor_concentration,
                    "current_pct": current.vendor_concentration,
                },
            )
        )
    return results


def _check_ar_zero_amounts(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    scope = ctx.scope
    base = _invoice_query(db, ctx.org_id, scope)
    row_count = base.with_entities(func.count(Invoice.id)).scalar() or 0
    total = base.with_entities(func.sum(Invoice.amount)).scalar() or 0
    if row_count <= 0 or float(total or 0) > 0:
        return []
    return [
        RuleFinding(
            finding_type="ar_amount_unmapped",
            title="AR amounts could not be read",
            detail=(
                f"{row_count} receivable row(s) were ingested but all amounts are $0. "
                "Column mapping may not have matched your export headers."
            ),
            severity="high",
            confidence=0.95,
            business_impact="data_quality",
            department="finance",
            category="data_quality",
            suggested_action=(
                "Re-export with Amount, Balance, or Total columns, or use aging bucket columns."
            ),
            evidence={"row_count": row_count, "total_ar": 0},
        )
    ]


def _check_ar_aging_spike(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    scope = ctx.scope
    base = _invoice_query(db, ctx.org_id, scope)
    over_90 = (
        base.filter(Invoice.days_overdue >= 90).with_entities(func.sum(Invoice.amount)).scalar() or 0
    )
    total = base.with_entities(func.sum(Invoice.amount)).scalar() or 0
    if total <= 0:
        return []
    pct = (over_90 / total) * 100
    if pct < 15:
        return []
    return [
        RuleFinding(
            finding_type="ar_aging_spike",
            title="AR over 90 days elevated",
            detail=f"Receivables over 90 days represent {pct:.1f}% of total AR (${over_90:,.0f}).",
            severity="high" if pct > 25 else "medium",
            confidence=0.95,
            business_impact="cash_flow",
            department="finance",
            category="financial",
            suggested_action="Review top overdue accounts and collection workflow.",
            evidence={
                "total_ar": float(total),
                "ar_over_90": float(over_90),
                "ar_over_90_pct": round(pct, 1),
            },
        )
    ]


def _check_customer_concentration(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    scope = ctx.scope
    rows = (
        _invoice_query(db, ctx.org_id, scope)
        .with_entities(Invoice.customer_id, func.sum(Invoice.amount))
        .group_by(Invoice.customer_id)
        .all()
    )
    totals = [(cid, float(amt or 0)) for cid, amt in rows if (amt or 0) > 0]
    if len(totals) < 3:
        return []
    grand_total = sum(amt for _, amt in totals)
    if grand_total <= 0:
        return []
    top_cid, top_amt = max(totals, key=lambda x: x[1])
    pct = (top_amt / grand_total) * 100
    if pct < 25:
        return []
    name_row = (
        db.query(Customer.name)
        .filter(Customer.org_id == ctx.org_id, Customer.customer_id == top_cid)
        .first()
    )
    name = (name_row[0] if name_row else None) or top_cid
    return [
        RuleFinding(
            finding_type="customer_concentration",
            title="Customer concentration risk",
            detail=(
                f"{name} represents {pct:.1f}% of total receivables "
                f"(${top_amt:,.0f} of ${grand_total:,.0f})."
            ),
            severity="high" if pct >= 35 else "medium",
            confidence=0.92,
            business_impact="cash_flow",
            department="finance",
            category="risk",
            suggested_action=f"Assess credit exposure to {name} and diversify the customer base.",
            evidence={
                "amount": top_amt,
                "pct_of_ar": round(pct, 1),
                "total_ar": grand_total,
                "top_customer_name": name,
            },
        )
    ]


def _check_duplicate_customers(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    """Same customer name with multiple distinct customer IDs."""
    q = db.query(Customer).filter(Customer.org_id == ctx.org_id)
    if ctx.source_job_ids:
        q = q.filter(Customer.source_job_id.in_(ctx.source_job_ids))
    by_name: dict[str, set[str]] = {}
    for customer in q.all():
        key = _normalize_name(customer.name)
        if key:
            by_name.setdefault(key, set()).add(customer.customer_id)
    dupes = {name: ids for name, ids in by_name.items() if len(ids) > 1}
    if not dupes:
        return []
    return [
        RuleFinding(
            finding_type="duplicate_customer_names",
            title="Duplicate customer names detected",
            detail=f"Found {len(dupes)} customer name(s) mapped to multiple IDs in exports.",
            severity="medium",
            confidence=1.0,
            business_impact="compliance",
            department="finance",
            category="data_quality",
            suggested_action="Reconcile customer master data in your ERP.",
            evidence={"duplicate_name_count": len(dupes)},
        )
    ]


def _check_ap_negative(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    negatives = _vendor_query(db, ctx.org_id, ctx.scope).filter(Vendor.balance < 0).all()
    if not negatives:
        return []
    neg_total = sum(v.balance or 0 for v in negatives)
    return [
        RuleFinding(
            finding_type="ap_negative_balance",
            title="AP negative balances found",
            detail=f"{len(negatives)} vendor(s) show negative AP balances.",
            severity="medium",
            confidence=1.0,
            business_impact="cash_flow",
            department="finance",
            category="financial",
            suggested_action="Verify vendor credits and payment applications.",
            evidence={"negative_vendor_count": len(negatives), "negative_total": neg_total},
        )
    ]


def _check_vendor_concentration(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    vendors = _vendor_query(db, ctx.org_id, ctx.scope).filter(Vendor.balance > 0).all()
    if len(vendors) < 3:
        return []
    total = sum(v.balance or 0 for v in vendors)
    if total <= 0:
        return []
    top = max(vendors, key=lambda v: v.balance or 0)
    pct = ((top.balance or 0) / total) * 100
    if pct < 40:
        return []
    return [
        RuleFinding(
            finding_type="vendor_concentration",
            title="Vendor concentration risk",
            detail=f"Top vendor represents {pct:.1f}% of open AP.",
            severity="medium",
            confidence=0.9,
            business_impact="cash_flow",
            department="purchasing",
            category="risk",
            suggested_action="Diversify vendor base and review payment terms.",
            evidence={
                "top_vendor_pct": round(pct, 1),
                "total_ap": total,
                "top_vendor_name": top.name or top.vendor_id,
            },
        )
    ]


def _check_vendor_name_concentration(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    vendors = _vendor_query(db, ctx.org_id, ctx.scope).filter(Vendor.balance > 0).all()
    if len(vendors) < 3:
        return []
    total = sum(v.balance or 0 for v in vendors)
    if total <= 0:
        return []
    by_name: dict[str, dict] = {}
    for v in vendors:
        key = _normalize_name(v.name)
        if not key:
            continue
        entry = by_name.setdefault(key, {"name": v.name, "balance": 0.0, "ids": set()})
        entry["balance"] += v.balance or 0
        entry["ids"].add(v.vendor_id)
    if not by_name:
        return []
    top = max(by_name.values(), key=lambda e: e["balance"])
    pct = (top["balance"] / total) * 100
    if len(top["ids"]) < 2 or pct < 40:
        return []
    return [
        RuleFinding(
            finding_type="vendor_name_concentration",
            title="Hidden vendor concentration (duplicate vendor records)",
            detail=(
                f"{top['name']} spans {len(top['ids'])} vendor IDs "
                f"({', '.join(sorted(top['ids']))}) totaling ${top['balance']:,.0f}, "
                f"or {pct:.1f}% of open AP — concealed by split records."
            ),
            severity="high",
            confidence=0.9,
            business_impact="cash_flow",
            department="purchasing",
            category="risk",
            suggested_action=(
                f"Merge duplicate records for {top['name']} and treat combined exposure as one vendor."
            ),
            evidence={
                "combined_pct": round(pct, 1),
                "vendor_id_count": len(top["ids"]),
                "combined_balance": top["balance"],
            },
        )
    ]


def _check_inventory_adjustments(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    adj_keywords = ["adjustment", "adj", "write-off", "writeoff", "shrinkage"]
    gl_rows = _gl_query(db, ctx.org_id, ctx.scope).all()
    adj_total = 0.0
    for row in gl_rows:
        name = (row.account_name or row.account_id or "").lower()
        if any(kw in name for kw in adj_keywords):
            adj_total += abs(row.amount)
    if adj_total < 5000:
        return []
    return [
        RuleFinding(
            finding_type="inventory_adjustment_spike",
            title="Inventory adjustments above baseline",
            detail=f"Inventory adjustment activity totals ${adj_total:,.0f} in current data.",
            severity="high",
            confidence=0.88,
            business_impact="margin",
            department="operations",
            category="operational",
            suggested_action="Require PO receiving validation before inventory adjustments.",
            evidence={"adjustment_total": adj_total},
        )
    ]


def _check_orphan_inventory(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    base = _inventory_query(db, ctx.org_id, ctx.scope)
    orphans = base.filter(
        (InventoryItem.gl_account == None) | (InventoryItem.gl_account == "")  # noqa: E711
    ).count()
    total = base.count()
    if orphans == 0:
        return []
    orphan_pct = (orphans / total * 100) if total else 0
    return [
        RuleFinding(
            finding_type="orphan_inventory",
            title="Orphan inventory items",
            detail=f"{orphans} inventory item(s) lack GL account mapping.",
            severity="medium",
            confidence=1.0,
            business_impact="inventory",
            department="operations",
            category="data_quality",
            suggested_action="Map inventory items to GL accounts in your ERP.",
            evidence={
                "orphan_count": orphans,
                "total_items": total,
                "orphan_pct": round(orphan_pct, 1),
            },
        )
    ]


def _check_negative_inventory(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    items = _inventory_query(db, ctx.org_id, ctx.scope).filter(InventoryItem.quantity < 0).all()
    if not items:
        return []
    total = _inventory_query(db, ctx.org_id, ctx.scope).count()
    return [
        RuleFinding(
            finding_type="negative_inventory",
            title="Negative inventory quantities",
            detail=(
                f"{len(items)} item(s) report negative on-hand quantity. "
                "Negative stock indicates unrecorded receipts or over-issued material."
            ),
            severity="high",
            confidence=1.0,
            business_impact="inventory",
            department="operations",
            category="operational",
            suggested_action="Cycle-count affected SKUs and correct on-hand balances in the ERP.",
            evidence={"negative_count": len(items), "total_items": total},
        )
    ]


def _check_zero_or_dead_stock_signals(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    base = _inventory_query(db, ctx.org_id, ctx.scope)
    zero = base.filter(InventoryItem.quantity == 0).count()
    total = base.count()
    if total == 0:
        return []
    pct = (zero / total) * 100
    if zero == 0 or pct < 25:
        return []
    return [
        RuleFinding(
            finding_type="zero_or_dead_stock",
            title="Widespread zero-stock items",
            detail=(
                f"{zero} of {total} inventory item(s) ({pct:.0f}%) are at zero on-hand — "
                "review for stockouts vs. obsolete SKUs to retire."
            ),
            severity="low",
            confidence=0.8,
            business_impact="inventory",
            department="operations",
            category="operational",
            suggested_action="Cross-check zero-stock SKUs against recent demand and open orders.",
            evidence={
                "zero_stock_count": zero,
                "total_items": total,
                "zero_stock_pct": round(pct, 1),
            },
        )
    ]


def _check_missing_gl_mappings(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    base = _gl_query(db, ctx.org_id, ctx.scope)
    missing = base.filter(
        (GlTransaction.account_id == None) | (GlTransaction.account_id == "")  # noqa: E711
    ).count()
    txn_count = base.count()
    if missing == 0:
        return []
    return [
        RuleFinding(
            finding_type="missing_gl_mappings",
            title="Missing GL account mappings",
            detail=f"{missing} transaction(s) have no account ID.",
            severity="high",
            confidence=1.0,
            business_impact="compliance",
            department="finance",
            category="data_quality",
            suggested_action="Complete GL mapping for all journal entries.",
            evidence={"unmapped_count": missing, "transaction_count": txn_count},
        )
    ]


def _check_invalid_aging_buckets(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    valid = {"current", "1-30", "31-60", "61-90", "91-120", "90+", ">90", "over 90"}
    invalid = (
        _invoice_query(db, ctx.org_id, ctx.scope)
        .filter(Invoice.aging_bucket != None, Invoice.aging_bucket != "")  # noqa: E711
        .all()
    )
    bad = [
        i
        for i in invalid
        if i.aging_bucket.lower() not in valid
        and not any(v in i.aging_bucket.lower() for v in ["90", "120"])
    ]
    if not bad:
        return []
    return [
        RuleFinding(
            finding_type="invalid_aging_buckets",
            title="Invalid AR aging buckets",
            detail=f"{len(bad)} invoice(s) use non-standard aging categories.",
            severity="low",
            confidence=0.85,
            business_impact="compliance",
            department="finance",
            category="data_quality",
            suggested_action="Standardize aging bucket definitions in AR reports.",
            evidence={"invalid_count": len(bad)},
        )
    ]


def _check_duplicate_vendors(db: Session, ctx: AnalysisContext) -> list[RuleFinding]:
    vendors = _vendor_query(db, ctx.org_id, ctx.scope).all()
    names: dict[str, list] = {}
    for v in vendors:
        key = (v.name or "").lower().strip()
        if key:
            names.setdefault(key, []).append(v.vendor_id)
    dupes = {k: v for k, v in names.items() if len(v) > 1}
    if not dupes:
        return []
    return [
        RuleFinding(
            finding_type="inconsistent_vendor_naming",
            title="Inconsistent vendor naming",
            detail=f"{len(dupes)} vendor name(s) appear with multiple IDs.",
            severity="medium",
            confidence=0.92,
            business_impact="cash_flow",
            department="purchasing",
            category="data_quality",
            suggested_action="Merge duplicate vendor records in AP master.",
            evidence={"duplicate_name_count": len(dupes)},
        )
    ]


# Re-export for backward compatibility
__all__ = [
    "RuleFinding",
    "RuleScope",
    "run_rules",
    "run_snapshot_delta_rules",
]
