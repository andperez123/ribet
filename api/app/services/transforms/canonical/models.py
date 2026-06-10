from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class CanonicalARRecord(BaseModel):
    customer_id: str
    customer_name: str | None = None
    invoice_id: str
    due_date: date | None = None
    amount: Decimal = Decimal("0")
    days_overdue: int = 0
    aging_bucket: str | None = None


class CanonicalAPRecord(BaseModel):
    vendor_id: str
    vendor_name: str | None = None
    balance: Decimal = Decimal("0")
    days_overdue: int = 0
    aging_bucket: str | None = None
    bucket_breakdown: dict[str, float] = Field(default_factory=dict)


class CanonicalGLTransaction(BaseModel):
    transaction_id: str
    account_id: str
    account_name: str | None = None
    amount: Decimal = Decimal("0")
    posted_at: str | None = None


class CanonicalGLTrialBalanceRow(BaseModel):
    account_id: str
    account_name: str | None = None
    beginning_balance: Decimal = Decimal("0")
    debits: Decimal = Decimal("0")
    credits: Decimal = Decimal("0")
    ending_balance: Decimal = Decimal("0")
    net_activity: Decimal = Decimal("0")
    analysis_amount: Decimal = Decimal("0")


class RejectedRow(BaseModel):
    row_index: int
    reason: str


class CanonicalInventoryItem(BaseModel):
    item_id: str
    sku: str
    quantity: Decimal = Decimal("0")
    gl_account: str | None = None


class CanonicalPurchaseOrder(BaseModel):
    po_id: str
    vendor_id: str
    vendor_name: str | None = None
    order_date: str | None = None
    promise_date: str | None = None
    due_date: str | None = None
    status: str | None = None
    line_amount: Decimal = Decimal("0")
    open_amount: Decimal = Decimal("0")
    days_late: int = 0
    sku: str | None = None
    qty_ordered: Decimal | None = None
    qty_received: Decimal | None = None


class CanonicalSalesOrder(BaseModel):
    order_id: str
    customer_id: str
    customer_name: str | None = None
    order_date: str | None = None
    ship_date: str | None = None
    promise_date: str | None = None
    status: str | None = None
    line_amount: Decimal = Decimal("0")
    open_amount: Decimal = Decimal("0")
    days_late: int = 0
    sku: str | None = None
    qty_ordered: Decimal | None = None
    qty_open: Decimal | None = None


class CanonicalDataset(BaseModel):
    ar: list[CanonicalARRecord] = Field(default_factory=list)
    ap: list[CanonicalAPRecord] = Field(default_factory=list)
    gl: list[CanonicalGLTransaction] = Field(default_factory=list)
    gl_trial_balance: list[CanonicalGLTrialBalanceRow] = Field(default_factory=list)
    inventory: list[CanonicalInventoryItem] = Field(default_factory=list)
    purchase_orders: list[CanonicalPurchaseOrder] = Field(default_factory=list)
    sales_orders: list[CanonicalSalesOrder] = Field(default_factory=list)
    normalized_rows: int = 0
    rejected_rows: list[RejectedRow] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    coverage_score: float = 0.0


class OperationalSnapshotData(BaseModel):
    period: str
    cash_position: float | None = None
    ar_over_90_pct: float | None = None
    ar_total: float | None = None
    ap_total: float | None = None
    inventory_value: float | None = None
    inventory_turns: float | None = None
    vendor_concentration: float | None = None
    health_score: int = 0
    health_status: str = "Stable"
    metrics: dict = Field(default_factory=dict)
