from __future__ import annotations

"""Comprehensive data digest computed from canonical tables.

This is the factual substrate the analysis layer reasons over. Unlike the
narrow per-rule queries, the digest summarizes the *entire* dataset — totals,
distributions, and top-N breakdowns — so both the executive summary and the
LLM analyst can synthesize over the same numbers the rules see.
"""

from dataclasses import asdict, dataclass, field
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Customer, GlTransaction, InventoryItem, Invoice, Vendor

ADJ_KEYWORDS = ["adjustment", "adj", "write-off", "writeoff", "shrinkage"]


def _normalize_name(name: str | None) -> str:
    return " ".join((name or "").lower().split())


@dataclass
class TopEntry:
    label: str
    amount: float
    pct: float
    detail: str = ""


@dataclass
class DataDigest:
    ar_total: float = 0.0
    ar_over_90: float = 0.0
    ar_over_90_pct: float = 0.0
    ar_invoice_count: int = 0
    top_customers: list[TopEntry] = field(default_factory=list)

    ap_total: float = 0.0
    ap_negative_total: float = 0.0
    vendor_count: int = 0
    top_vendors: list[TopEntry] = field(default_factory=list)

    gl_txn_count: int = 0
    gl_adjustment_total: float = 0.0
    gl_unmapped_count: int = 0

    inventory_item_count: int = 0
    inventory_total_qty: float = 0.0
    inventory_negative_count: int = 0
    inventory_zero_count: int = 0
    inventory_orphan_count: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["top_customers"] = [asdict(t) for t in self.top_customers]
        d["top_vendors"] = [asdict(t) for t in self.top_vendors]
        return d


def build_data_digest(db: Session, org_id: UUID, top_n: int = 5) -> DataDigest:
    digest = DataDigest()

    # --- Accounts Receivable ---
    digest.ar_total = float(
        db.query(func.sum(Invoice.amount)).filter(Invoice.org_id == org_id).scalar() or 0
    )
    digest.ar_over_90 = float(
        db.query(func.sum(Invoice.amount))
        .filter(Invoice.org_id == org_id, Invoice.days_overdue >= 90)
        .scalar()
        or 0
    )
    digest.ar_over_90_pct = (
        (digest.ar_over_90 / digest.ar_total * 100) if digest.ar_total > 0 else 0.0
    )
    digest.ar_invoice_count = (
        db.query(func.count(Invoice.id)).filter(Invoice.org_id == org_id).scalar() or 0
    )

    cust_names = {
        c.customer_id: c.name
        for c in db.query(Customer).filter(Customer.org_id == org_id).all()
    }
    cust_rows = (
        db.query(Invoice.customer_id, func.sum(Invoice.amount))
        .filter(Invoice.org_id == org_id)
        .group_by(Invoice.customer_id)
        .all()
    )
    cust_totals = sorted(
        ((cid, float(amt or 0)) for cid, amt in cust_rows),
        key=lambda x: x[1],
        reverse=True,
    )
    for cid, amt in cust_totals[:top_n]:
        digest.top_customers.append(
            TopEntry(
                label=cust_names.get(cid) or cid,
                amount=amt,
                pct=(amt / digest.ar_total * 100) if digest.ar_total > 0 else 0.0,
            )
        )

    # --- Accounts Payable (name-normalized to combine split vendor records) ---
    vendors = db.query(Vendor).filter(Vendor.org_id == org_id).all()
    digest.vendor_count = len(vendors)
    digest.ap_negative_total = float(sum(v.balance or 0 for v in vendors if (v.balance or 0) < 0))
    positive = [v for v in vendors if (v.balance or 0) > 0]
    digest.ap_total = float(sum(v.balance or 0 for v in positive))
    by_name: dict[str, dict] = {}
    for v in positive:
        key = _normalize_name(v.name) or v.vendor_id
        entry = by_name.setdefault(key, {"name": v.name or v.vendor_id, "balance": 0.0, "ids": set()})
        entry["balance"] += v.balance or 0
        entry["ids"].add(v.vendor_id)
    for entry in sorted(by_name.values(), key=lambda e: e["balance"], reverse=True)[:top_n]:
        ids = sorted(entry["ids"])
        digest.top_vendors.append(
            TopEntry(
                label=entry["name"],
                amount=entry["balance"],
                pct=(entry["balance"] / digest.ap_total * 100) if digest.ap_total > 0 else 0.0,
                detail=f"{len(ids)} vendor ID(s): {', '.join(ids)}" if len(ids) > 1 else "",
            )
        )

    # --- General Ledger ---
    gl_rows = db.query(GlTransaction).filter(GlTransaction.org_id == org_id).all()
    digest.gl_txn_count = len(gl_rows)
    digest.gl_adjustment_total = float(
        sum(
            abs(r.amount)
            for r in gl_rows
            if any(kw in (r.account_name or r.account_id or "").lower() for kw in ADJ_KEYWORDS)
        )
    )
    digest.gl_unmapped_count = sum(1 for r in gl_rows if not (r.account_id or "").strip())

    # --- Inventory ---
    inv = db.query(InventoryItem).filter(InventoryItem.org_id == org_id).all()
    digest.inventory_item_count = len(inv)
    digest.inventory_total_qty = float(sum(i.quantity or 0 for i in inv))
    digest.inventory_negative_count = sum(1 for i in inv if (i.quantity or 0) < 0)
    digest.inventory_zero_count = sum(1 for i in inv if (i.quantity or 0) == 0)
    digest.inventory_orphan_count = sum(1 for i in inv if not (i.gl_account or "").strip())

    return digest


def build_executive_summary(digest: DataDigest, findings, max_items: int = 6) -> list[str]:
    """Synthesize a quantified executive summary from the digest + findings.

    Unlike the old behavior (top-5 finding titles), this surfaces the largest
    dollar exposures and material data-integrity issues with concrete numbers.
    """
    lines: list[str] = []

    if digest.ar_total > 0:
        lines.append(
            f"Total receivables of ${digest.ar_total:,.0f} across {digest.ar_invoice_count} "
            f"invoice(s); ${digest.ar_over_90:,.0f} ({digest.ar_over_90_pct:.0f}%) is over 90 days."
        )
    if digest.top_customers:
        tc = digest.top_customers[0]
        if tc.pct >= 20:
            lines.append(
                f"{tc.label} is the largest receivable at ${tc.amount:,.0f} ({tc.pct:.0f}% of AR)."
            )
    if digest.top_vendors:
        tv = digest.top_vendors[0]
        concentration_note = f" across {tv.detail}" if tv.detail else ""
        if tv.pct >= 30:
            lines.append(
                f"Top supplier {tv.label} carries ${tv.amount:,.0f} of open AP "
                f"({tv.pct:.0f}%){concentration_note}."
            )
    if digest.gl_adjustment_total > 0:
        lines.append(
            f"Inventory/GL adjustment activity totals ${digest.gl_adjustment_total:,.0f}."
        )
    integrity_bits = []
    if digest.inventory_negative_count:
        integrity_bits.append(f"{digest.inventory_negative_count} negative-stock item(s)")
    if digest.gl_unmapped_count:
        integrity_bits.append(f"{digest.gl_unmapped_count} unmapped GL entry(ies)")
    if digest.inventory_orphan_count:
        integrity_bits.append(f"{digest.inventory_orphan_count} unmapped inventory item(s)")
    if integrity_bits:
        lines.append("Data integrity issues: " + ", ".join(integrity_bits) + ".")

    crit = [f for f in findings if f.severity in ("critical", "high")]
    if crit:
        lines.append(
            f"{len(crit)} high-severity finding(s) require attention this period."
        )

    if not lines:
        lines.append("No significant operational risks detected in current data.")
    return lines[:max_items]
