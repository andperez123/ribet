from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

InsightSeverity = Literal["info", "watch", "alert"]
NarrationStatus = Literal["completed", "skipped", "failed", "legacy", "fallback"]


class TopEntryOut(BaseModel):
    label: str = ""
    amount: float = 0.0
    pct: float = 0.0
    detail: str = ""


class DataDigestOut(BaseModel):
    ar_total: float = 0.0
    ar_over_90: float = 0.0
    ar_over_90_pct: float = 0.0
    ar_invoice_count: int = 0
    top_customers: list[TopEntryOut] = Field(default_factory=list)

    ap_total: float = 0.0
    ap_negative_total: float = 0.0
    vendor_count: int = 0
    top_vendors: list[TopEntryOut] = Field(default_factory=list)
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


class DomainInsightOut(BaseModel):
    domain: str
    title: str
    body: str
    severity: InsightSeverity
    metric_label: str | None = None
    metric_value: str | None = None
    finding_type: str | None = None
    source_label: str | None = None


class DataCoverageOut(BaseModel):
    ar: bool = False
    ap: bool = False
    gl: bool = False
    inventory: bool = False
    purchase_orders: bool = False
    sales_orders: bool = False
    ar_present: bool = False
    ar_unmapped: bool = False
    ap_aging_available: bool = False
    primary_domain: str | None = None


class AnalysisMetadataOut(BaseModel):
    narration: NarrationStatus = "legacy"
    model: str | None = None
    finding_count: int = 0
    narrated_count: int = 0
    data_domains_present: list[str] = Field(default_factory=list)
    duration_ms: int | None = None
    insights_source: str | None = None
