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
    ap_current: float = 0.0
    ap_1_30: float = 0.0
    ap_31_60: float = 0.0
    ap_61_90: float = 0.0
    ap_91_plus: float = 0.0
    ap_over_60_pct: float = 0.0

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


_REPORT_TYPE_DOMAINS: dict[str, set[str]] = {
    "ar_aging": {"ar"},
    "ap_aging": {"ap"},
    "gl_detail": {"gl"},
    "inventory": {"inventory"},
}


def domains_for_report_type(report_type: str | None) -> set[str] | None:
    if not report_type:
        return None
    return _REPORT_TYPE_DOMAINS.get(report_type)


def build_data_digest(
    db: Session,
    org_id: UUID,
    top_n: int = 5,
    period: str | None = None,
    source_job_ids: list[UUID] | None = None,
    domains: set[str] | None = None,
) -> DataDigest:
    digest = DataDigest()
    include_ar = domains is None or "ar" in domains
    include_ap = domains is None or "ap" in domains
    include_gl = domains is None or "gl" in domains
    include_inventory = domains is None or "inventory" in domains

    def _apply_job_filter(q, model):
        if source_job_ids:
            q = q.filter(model.source_job_id.in_(source_job_ids))
        return q

    def _invoice_q():
        q = db.query(Invoice).filter(Invoice.org_id == org_id)
        if period:
            q = q.filter(Invoice.period_label == period)
        return _apply_job_filter(q, Invoice)

    def _vendor_q():
        q = db.query(Vendor).filter(Vendor.org_id == org_id)
        if period:
            q = q.filter(Vendor.period_label == period)
        return _apply_job_filter(q, Vendor)

    def _gl_q():
        q = db.query(GlTransaction).filter(GlTransaction.org_id == org_id)
        if period:
            q = q.filter(GlTransaction.period_label == period)
        return _apply_job_filter(q, GlTransaction)

    def _inv_q():
        q = db.query(InventoryItem).filter(InventoryItem.org_id == org_id)
        if period:
            q = q.filter(InventoryItem.period_label == period)
        return _apply_job_filter(q, InventoryItem)

    # --- Accounts Receivable ---
    if not include_ar:
        inv_base = _invoice_q().filter(Invoice.id == None)  # noqa: E711
    else:
        inv_base = _invoice_q()
    digest.ar_total = float(
        inv_base.with_entities(func.sum(Invoice.amount)).scalar() or 0
    )
    digest.ar_over_90 = float(
        inv_base.filter(Invoice.days_overdue >= 90)
        .with_entities(func.sum(Invoice.amount))
        .scalar()
        or 0
    )
    digest.ar_over_90_pct = (
        (digest.ar_over_90 / digest.ar_total * 100) if digest.ar_total > 0 else 0.0
    )
    digest.ar_invoice_count = inv_base.count()

    cust_names = {
        c.customer_id: c.name
        for c in db.query(Customer).filter(Customer.org_id == org_id).all()
    }
    cust_rows = (
        inv_base.with_entities(Invoice.customer_id, func.sum(Invoice.amount))
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
    if include_ap:
        vendors = _vendor_q().all()
        digest.vendor_count = len(vendors)
        digest.ap_negative_total = float(sum(v.balance or 0 for v in vendors if (v.balance or 0) < 0))
        positive = [v for v in vendors if (v.balance or 0) > 0]
        digest.ap_total = float(sum(v.balance or 0 for v in positive))
        bucket_totals = {"current": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "91_plus": 0.0, "over_120": 0.0}
        for v in positive:
            breakdown = v.bucket_breakdown or {}
            for key, amt in breakdown.items():
                if key in bucket_totals:
                    bucket_totals[key] += float(amt or 0)
        digest.ap_current = bucket_totals["current"]
        digest.ap_1_30 = bucket_totals["1_30"]
        digest.ap_31_60 = bucket_totals["31_60"]
        digest.ap_61_90 = bucket_totals["61_90"]
        digest.ap_91_plus = bucket_totals["91_plus"] + bucket_totals["over_120"]
        bucket_sum = sum(bucket_totals.values())
        if bucket_sum > 0:
            over_60 = digest.ap_31_60 + digest.ap_61_90 + digest.ap_91_plus
            digest.ap_over_60_pct = over_60 / bucket_sum * 100
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
    if not include_gl:
        gl_rows = []
    else:
        gl_rows = _gl_q().all()
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
    if not include_inventory:
        inv = []
    else:
        inv = _inv_q().all()
    digest.inventory_item_count = len(inv)
    digest.inventory_total_qty = float(sum(i.quantity or 0 for i in inv))
    digest.inventory_negative_count = sum(1 for i in inv if (i.quantity or 0) < 0)
    digest.inventory_zero_count = sum(1 for i in inv if (i.quantity or 0) == 0)
    digest.inventory_orphan_count = sum(1 for i in inv if not (i.gl_account or "").strip())

    return digest


def build_data_coverage(
    digest: DataDigest,
    *,
    primary_domain: str | None = None,
) -> dict:
    ap_buckets = (
        digest.ap_current + digest.ap_1_30 + digest.ap_31_60 + digest.ap_61_90 + digest.ap_91_plus
    )
    coverage = {
        "ar": digest.ar_total > 0,
        "ap": digest.ap_total > 0,
        "gl": digest.gl_txn_count > 0,
        "inventory": digest.inventory_item_count > 0,
        "ar_present": digest.ar_invoice_count > 0,
        "ar_unmapped": digest.ar_invoice_count > 0 and digest.ar_total <= 0,
        "ap_aging_available": ap_buckets > 0,
    }
    if primary_domain:
        coverage["primary_domain"] = primary_domain
    return coverage


def digest_has_data(digest: DataDigest) -> bool:
    cov = build_data_coverage(digest)
    return any(cov.get(k) for k in ("ar", "ap", "gl", "inventory"))


@dataclass
class DomainInsight:
    domain: str
    title: str
    body: str
    severity: str
    metric_label: str | None = None
    metric_value: str | None = None
    finding_type: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


_FINDING_DOMAIN: dict[str, str] = {
    "ar_aging_spike": "ar",
    "customer_concentration": "ar",
    "duplicate_customers": "ar",
    "invalid_aging_buckets": "ar",
    "ap_negative_balance": "ap",
    "vendor_concentration": "ap",
    "vendor_name_concentration": "ap",
    "inconsistent_vendor_naming": "ap",
    "duplicate_vendors": "ap",
    "inventory_adjustment_spike": "inventory",
    "orphan_inventory": "inventory",
    "negative_inventory": "inventory",
    "zero_or_dead_stock": "inventory",
    "missing_gl_mappings": "gl",
    "operational_cash_pressure": "risk",
}


def _finding_severity_to_insight(severity: str) -> str:
    if severity in ("critical", "high"):
        return "alert"
    if severity == "medium":
        return "watch"
    return "info"


def build_domain_insights(digest: DataDigest, findings) -> list[DomainInsight]:
    """Always-on insight cards from digest + rule findings."""
    insights: list[DomainInsight] = []
    seen_fingerprints: set[str] = set()

    if digest.ar_invoice_count > 0 and digest.ar_total <= 0:
        insights.append(
            DomainInsight(
                domain="data_quality",
                title="AR amounts not detected",
                body=(
                    f"{digest.ar_invoice_count} AR row(s) were ingested but all amounts are $0. "
                    "Your file may use aging bucket columns or unrecognized balance headers."
                ),
                severity="alert",
                metric_label="Rows ingested",
                metric_value=str(digest.ar_invoice_count),
            )
        )
    elif digest.ar_total > 0 or digest.ar_invoice_count > 0:
        ar_sev = "watch" if digest.ar_over_90_pct >= 10 else "info"
        if digest.ar_over_90_pct >= 15:
            ar_sev = "alert"
        insights.append(
            DomainInsight(
                domain="ar",
                title="Accounts receivable",
                body=(
                    f"${digest.ar_total:,.0f} across {digest.ar_invoice_count} invoice(s); "
                    f"${digest.ar_over_90:,.0f} ({digest.ar_over_90_pct:.1f}%) is over 90 days."
                ),
                severity=ar_sev,
                metric_label="AR over 90",
                metric_value=f"{digest.ar_over_90_pct:.1f}%",
            )
        )
        for tc in digest.top_customers[:3]:
            if tc.amount <= 0:
                continue
            insights.append(
                DomainInsight(
                    domain="ar",
                    title=f"Customer: {tc.label}",
                    body=f"${tc.amount:,.0f} ({tc.pct:.1f}% of total receivables).",
                    severity="watch" if tc.pct >= 25 else "info",
                    metric_label="Share of AR",
                    metric_value=f"{tc.pct:.1f}%",
                )
            )

    if digest.ap_total > 0 or digest.vendor_count > 0:
        top_pct = digest.top_vendors[0].pct if digest.top_vendors else 0.0
        ap_sev = "alert" if top_pct >= 40 else ("watch" if top_pct >= 30 else "info")
        insights.append(
            DomainInsight(
                domain="ap",
                title="Accounts payable",
                body=(
                    f"${digest.ap_total:,.0f} open across {digest.vendor_count} vendor record(s)."
                    + (
                        f" ${abs(digest.ap_negative_total):,.0f} in negative balances."
                        if digest.ap_negative_total < 0
                        else ""
                    )
                ),
                severity=ap_sev,
                metric_label="Open AP",
                metric_value=f"${digest.ap_total:,.0f}",
            )
        )
        for tv in digest.top_vendors[:3]:
            detail_note = f" {tv.detail}." if tv.detail else "."
            insights.append(
                DomainInsight(
                    domain="ap",
                    title=f"Vendor: {tv.label}",
                    body=f"${tv.amount:,.0f} ({tv.pct:.1f}% of open AP).{detail_note}",
                    severity="watch" if tv.pct >= 30 else "info",
                    metric_label="Share of AP",
                    metric_value=f"{tv.pct:.1f}%",
                )
            )
        ap_bucket_total = (
            digest.ap_current + digest.ap_1_30 + digest.ap_31_60 + digest.ap_61_90 + digest.ap_91_plus
        )
        if ap_bucket_total > 0:
            overdue = digest.ap_31_60 + digest.ap_61_90 + digest.ap_91_plus
            overdue_pct = overdue / ap_bucket_total * 100
            ap_age_sev = "alert" if overdue_pct >= 50 else ("watch" if overdue_pct >= 30 else "info")
            insights.append(
                DomainInsight(
                    domain="ap",
                    title="AP aging breakdown",
                    body=(
                        f"${digest.ap_current:,.0f} current, ${digest.ap_31_60:,.0f} in 31–60 days, "
                        f"${digest.ap_61_90:,.0f} in 61–90 days, ${digest.ap_91_plus:,.0f} over 90 days."
                    ),
                    severity=ap_age_sev,
                    metric_label="AP over 60 days",
                    metric_value=f"{digest.ap_over_60_pct:.1f}%",
                )
            )

    if digest.gl_txn_count > 0:
        gl_sev = "info"
        if digest.gl_unmapped_count or digest.gl_adjustment_total >= 5000:
            gl_sev = "watch"
        insights.append(
            DomainInsight(
                domain="gl",
                title="General ledger",
                body=(
                    f"{digest.gl_txn_count} transaction(s); "
                    f"${digest.gl_adjustment_total:,.0f} in adjustment activity."
                    + (
                        f" {digest.gl_unmapped_count} unmapped entry(ies)."
                        if digest.gl_unmapped_count
                        else ""
                    )
                ),
                severity=gl_sev,
                metric_label="GL transactions",
                metric_value=str(digest.gl_txn_count),
            )
        )

    if digest.inventory_item_count > 0:
        integrity = (
            digest.inventory_negative_count
            + digest.inventory_orphan_count
            + digest.inventory_zero_count
        )
        inv_sev = "watch" if integrity else "info"
        if digest.inventory_negative_count:
            inv_sev = "alert"
        insights.append(
            DomainInsight(
                domain="inventory",
                title="Inventory",
                body=(
                    f"{digest.inventory_item_count} item(s); "
                    f"{digest.inventory_total_qty:,.0f} total units on hand."
                    + (
                        f" {digest.inventory_negative_count} negative, "
                        f"{digest.inventory_zero_count} at zero, "
                        f"{digest.inventory_orphan_count} unmapped."
                        if integrity
                        else " No integrity issues detected."
                    )
                ),
                severity=inv_sev,
                metric_label="Items tracked",
                metric_value=str(digest.inventory_item_count),
            )
        )

    for f in findings:
        fp = getattr(f, "fingerprint", None) or f"{f.finding_type}:{f.title}"
        if fp in seen_fingerprints:
            continue
        seen_fingerprints.add(fp)
        domain = _FINDING_DOMAIN.get(f.finding_type, getattr(f, "category", "operational"))
        insights.append(
            DomainInsight(
                domain=domain,
                title=f.title,
                body=f.detail,
                severity=_finding_severity_to_insight(f.severity),
                finding_type=f.finding_type,
            )
        )

    return insights


def build_executive_summary(digest: DataDigest, findings, max_items: int = 8) -> list[str]:
    """Deterministic executive bullets from digest + findings (no LLM text)."""
    lines: list[str] = []

    if digest.ar_invoice_count > 0 and digest.ar_total <= 0:
        lines.append(
            f"AR file has {digest.ar_invoice_count} row(s) but receivable amounts could not be "
            "read — check that your export includes Amount, Balance, Total, or aging bucket columns."
        )
    elif digest.ar_total > 0 or digest.ar_invoice_count > 0:
        lines.append(
            f"Total receivables of ${digest.ar_total:,.0f} across {digest.ar_invoice_count} "
            f"invoice(s); ${digest.ar_over_90:,.0f} ({digest.ar_over_90_pct:.1f}%) is over 90 days."
        )
    if digest.top_customers:
        tc = digest.top_customers[0]
        if tc.amount > 0:
            lines.append(
                f"Largest customer {tc.label} at ${tc.amount:,.0f} ({tc.pct:.1f}% of AR)."
            )
    if digest.ap_total > 0 or digest.vendor_count > 0:
        lines.append(
            f"Open payables of ${digest.ap_total:,.0f} across {digest.vendor_count} vendor record(s)."
        )
    if digest.top_vendors:
        tv = digest.top_vendors[0]
        concentration_note = f" ({tv.detail})" if tv.detail else ""
        lines.append(
            f"Top supplier {tv.label} carries ${tv.amount:,.0f} of open AP "
            f"({tv.pct:.1f}%){concentration_note}."
        )
    if digest.gl_txn_count > 0:
        lines.append(
            f"General ledger: {digest.gl_txn_count} transaction(s); "
            f"${digest.gl_adjustment_total:,.0f} in adjustment activity."
        )
    if digest.inventory_item_count > 0:
        lines.append(
            f"Inventory: {digest.inventory_item_count} item(s), "
            f"{digest.inventory_total_qty:,.0f} total units on hand."
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
        lines.append(f"{len(crit)} high-severity finding(s) require attention this period.")

    if not lines:
        lines.append(
            "No canonical financial data found for this org. "
            "Upload AR/AP/GL/inventory exports to generate insights."
        )
    return lines[:max_items]


def build_weekly_brief_sections(
    digest: DataDigest,
    findings,
    coverage: dict[str, bool],
    trends: list[str] | None = None,
) -> dict[str, list[str]]:
    """Digest-driven weekly brief sections. Omits domains with no data."""
    sections: dict[str, list[str]] = {}
    finding_titles = {f.finding_type: f.title for f in findings}

    if coverage.get("ar"):
        items: list[str] = [
            f"Receivables total ${digest.ar_total:,.0f}; "
            f"{digest.ar_over_90_pct:.1f}% (${digest.ar_over_90:,.0f}) is over 90 days."
        ]
        if digest.ar_over_90_pct < 15:
            items.append("AR aging is within the 15% alert threshold.")
        for f in findings:
            if f.business_impact == "cash_flow" or f.finding_type == "ar_aging_spike":
                items.append(f.title)
        sections["cash_position"] = items

    if coverage.get("ap"):
        items = [f"Open payables ${digest.ap_total:,.0f} across {digest.vendor_count} vendor(s)."]
        if digest.ap_negative_total < 0:
            items.append(f"${abs(digest.ap_negative_total):,.0f} in negative vendor balances.")
        for f in findings:
            if f.finding_type in ("ap_negative_balance", "inconsistent_vendor_naming", "duplicate_vendors"):
                items.append(f.title)
        sections["ap_aging"] = items

    if coverage.get("ap") and digest.top_vendors:
        tv = digest.top_vendors[0]
        items = [f"Top vendor {tv.label} is {tv.pct:.1f}% of open AP (${tv.amount:,.0f})."]
        if "vendor_concentration" in finding_titles or "vendor_name_concentration" in finding_titles:
            for ft in ("vendor_concentration", "vendor_name_concentration"):
                if ft in finding_titles:
                    items.append(finding_titles[ft])
        elif tv.pct < 40:
            items.append("Vendor concentration is below the 40% alert threshold.")
        sections["vendor_concentration"] = items

    if coverage.get("gl") or coverage.get("inventory"):
        items = []
        if digest.gl_adjustment_total > 0:
            items.append(f"GL adjustment activity totals ${digest.gl_adjustment_total:,.0f}.")
        if digest.inventory_negative_count or digest.inventory_orphan_count:
            items.append(
                f"Inventory integrity: {digest.inventory_negative_count} negative, "
                f"{digest.inventory_orphan_count} unmapped item(s)."
            )
        for f in findings:
            if f.finding_type in (
                "inventory_adjustment_spike",
                "orphan_inventory",
                "negative_inventory",
                "zero_or_dead_stock",
            ):
                items.append(f.title)
        if not items and coverage.get("inventory"):
            items.append(
                f"{digest.inventory_item_count} inventory item(s) tracked; "
                "no adjustment or integrity alerts."
            )
        if items:
            sections["inventory_adjustments"] = items

    dup_items = [f.title for f in findings if "duplicate" in f.finding_type]
    if dup_items:
        sections["duplicate_invoices"] = dup_items

    if trends:
        sections["summary"] = trends[:3]

    return sections

