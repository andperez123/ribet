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


class CanonicalGLTransaction(BaseModel):
    transaction_id: str
    account_id: str
    account_name: str | None = None
    amount: Decimal = Decimal("0")
    posted_at: str | None = None


class CanonicalInventoryItem(BaseModel):
    item_id: str
    sku: str
    quantity: Decimal = Decimal("0")
    gl_account: str | None = None


class CanonicalDataset(BaseModel):
    ar: list[CanonicalARRecord] = Field(default_factory=list)
    ap: list[CanonicalAPRecord] = Field(default_factory=list)
    gl: list[CanonicalGLTransaction] = Field(default_factory=list)
    inventory: list[CanonicalInventoryItem] = Field(default_factory=list)


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
