from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.services.rules.types import RuleFinding


@dataclass(frozen=True)
class FindingSpec:
    finding_id: str
    domain: str
    source_metric_keys: tuple[str, ...] = ()


FINDING_REGISTRY: dict[str, FindingSpec] = {
    "customer_concentration": FindingSpec(
        "F-AR-001",
        "ar",
        (
            "metrics.ar.total_receivables",
            "metrics.ar.top_customer.amount",
            "metrics.ar.top_customer.percent_of_total",
        ),
    ),
    "duplicate_customer_names": FindingSpec(
        "F-AR-002",
        "ar",
        ("metrics.ar.invoice_count",),
    ),
    "ar_amount_unmapped": FindingSpec(
        "F-AR-003",
        "ar",
        ("metrics.ar.invoice_count", "metrics.ar.total_receivables"),
    ),
    "ar_aging_spike": FindingSpec(
        "F-AR-004",
        "ar",
        (
            "metrics.ar.total_receivables",
            "metrics.ar.over_90_amount",
            "metrics.ar.over_90_percent",
        ),
    ),
    "invalid_aging_buckets": FindingSpec(
        "F-AR-005",
        "ar",
        ("metrics.ar.invoice_count",),
    ),
    "ap_negative_balance": FindingSpec(
        "F-AP-001",
        "ap",
        ("metrics.ap.total_payables", "metrics.ap.negative_balance_total"),
    ),
    "vendor_concentration": FindingSpec(
        "F-AP-002",
        "ap",
        (
            "metrics.ap.total_payables",
            "metrics.ap.top_vendor.percent_of_total",
        ),
    ),
    "vendor_name_concentration": FindingSpec(
        "F-AP-003",
        "ap",
        (
            "metrics.ap.total_payables",
            "metrics.ap.top_vendor.percent_of_total",
        ),
    ),
    "inconsistent_vendor_naming": FindingSpec(
        "F-AP-004",
        "ap",
        ("metrics.ap.vendor_count",),
    ),
    "orphan_inventory": FindingSpec(
        "F-INV-001",
        "inventory",
        (
            "metrics.inventory.item_count",
            "metrics.inventory.orphan_count",
            "metrics.inventory.orphan_percent",
        ),
    ),
    "negative_inventory": FindingSpec(
        "F-INV-002",
        "inventory",
        (
            "metrics.inventory.item_count",
            "metrics.inventory.negative_count",
        ),
    ),
    "zero_or_dead_stock": FindingSpec(
        "F-INV-003",
        "inventory",
        (
            "metrics.inventory.item_count",
            "metrics.inventory.zero_stock_count",
            "metrics.inventory.zero_stock_percent",
        ),
    ),
    "inventory_adjustment_spike": FindingSpec(
        "F-GL-001",
        "gl",
        ("metrics.gl.adjustment_total",),
    ),
    "missing_gl_mappings": FindingSpec(
        "F-GL-002",
        "gl",
        (
            "metrics.gl.transaction_count",
            "metrics.gl.unmapped_count",
        ),
    ),
    "ar_aging_worsened": FindingSpec(
        "F-TREND-001",
        "ar",
        ("metrics.ar.over_90_percent",),
    ),
    "health_score_declined": FindingSpec(
        "F-TREND-002",
        "health",
        ("health.score", "health.prior_score"),
    ),
    "vendor_concentration_increased": FindingSpec(
        "F-TREND-003",
        "ap",
        ("metrics.ap.top_vendor.percent_of_total",),
    ),
    "operational_cash_pressure": FindingSpec(
        "F-XD-001",
        "cross",
        (
            "metrics.ar.over_90_percent",
            "metrics.inventory.total_units",
        ),
    ),
    "ar_ap_working_capital": FindingSpec(
        "F-XD-002",
        "cross",
        (
            "metrics.ar.over_90_percent",
            "metrics.ap.top_vendor.percent_of_total",
        ),
    ),
    "gl_inventory_writeoff_pattern": FindingSpec(
        "F-XD-003",
        "cross",
        (
            "metrics.gl.adjustment_total",
            "metrics.inventory.orphan_count",
        ),
    ),
    "po_vendor_late": FindingSpec(
        "F-PO-001",
        "orders",
        (
            "metrics.orders.late_po_total",
            "metrics.orders.late_po_count",
        ),
    ),
    "po_late_cluster": FindingSpec(
        "F-PO-002",
        "orders",
        (
            "metrics.orders.late_po_total",
            "metrics.orders.late_po_count",
        ),
    ),
    "so_past_due_ship": FindingSpec(
        "F-SO-001",
        "sales",
        (
            "metrics.sales.past_due_total",
            "metrics.sales.past_due_count",
        ),
    ),
    "so_backlog_at_risk": FindingSpec(
        "F-SO-002",
        "sales",
        (
            "metrics.sales.past_due_total",
            "metrics.sales.past_due_count",
        ),
    ),
    "po_so_fulfillment_gap": FindingSpec(
        "F-XD-004",
        "cross",
        (
            "metrics.orders.late_po_total",
            "metrics.sales.past_due_total",
        ),
    ),
}

# Legacy aliases for consumers that still reference old finding_type strings.
FINDING_TYPE_ALIASES: dict[str, str] = {
    "duplicate_customer_ids": "duplicate_customer_names",
    "duplicate_customers": "duplicate_customer_names",
    "duplicate_vendors": "inconsistent_vendor_naming",
    "gl_adjustment_spike": "inventory_adjustment_spike",
}


def resolve_finding_type(finding_type: str) -> str:
    return FINDING_TYPE_ALIASES.get(finding_type, finding_type)


def enrich_finding(finding: RuleFinding, period: str, org_id: UUID) -> RuleFinding:
    resolved = resolve_finding_type(finding.finding_type)
    spec = FINDING_REGISTRY.get(resolved)
    if spec:
        finding.finding_id = spec.finding_id
        finding.source_metric_keys = list(spec.source_metric_keys)
    else:
        finding.finding_id = f"F-UNK-{resolved[:8].upper()}"
        finding.source_metric_keys = []
    short_hash = finding.fingerprint[:5]
    finding.finding_instance_id = f"{finding.finding_id}-{period}-{short_hash}"
    return finding


def enrich_findings(
    findings: list[RuleFinding], period: str, org_id: UUID
) -> list[RuleFinding]:
    return [enrich_finding(f, period, org_id) for f in findings]
