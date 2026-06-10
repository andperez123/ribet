"""Row-level meaning inference — what one row represents."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.etl.classifier import DatasetClassification, LikelyType

ROW_MEANING_LABELS: dict[str, str] = {
    "one_invoice": "One row = one invoice",
    "one_gl_account_balance": "One row = one GL account balance",
    "one_gl_transaction": "One row = one journal entry",
    "one_inventory_item": "One row = one inventory item",
    "one_purchase_order_line": "One row = one purchase order line",
    "one_sales_order_line": "One row = one sales order line",
    "one_job_operation": "One row = one job operation",
    "one_timecard_punch": "One row = one timecard punch",
    "unknown": "Unknown — user must specify",
}

_TYPE_TO_ROW_MEANING: dict[str, tuple[str, float, list[str]]] = {
    "ar_aging": ("one_invoice", 0.88, ["AR aging exports typically list one invoice per row"]),
    "ap_aging": ("one_invoice", 0.85, ["AP aging exports typically list one vendor balance line per row"]),
    "gl_trial_balance": (
        "one_gl_account_balance",
        0.92,
        ["Trial balance exports list one GL account per row"],
    ),
    "gl_detail": ("one_gl_transaction", 0.88, ["GL detail exports list one journal entry per row"]),
    "inventory": ("one_inventory_item", 0.9, ["Inventory exports list one item per row"]),
    "purchase_orders": (
        "one_purchase_order_line",
        0.85,
        ["PO exports typically list one line or open PO per row"],
    ),
    "sales_orders": (
        "one_sales_order_line",
        0.85,
        ["Sales order exports typically list one line per row"],
    ),
    "jobs": ("one_job_operation", 0.75, ["Job exports often list one operation per row"]),
    "timecards": ("one_timecard_punch", 0.8, ["Timecard exports list one punch or entry per row"]),
    "unknown_operational_export": ("unknown", 0.2, ["Could not infer row meaning from headers"]),
    "unknown": ("unknown", 0.15, ["Could not infer row meaning"]),
}

ROW_MEANING_OPTIONS = [
    ("one_invoice", ROW_MEANING_LABELS["one_invoice"]),
    ("one_gl_account_balance", ROW_MEANING_LABELS["one_gl_account_balance"]),
    ("one_gl_transaction", ROW_MEANING_LABELS["one_gl_transaction"]),
    ("one_inventory_item", ROW_MEANING_LABELS["one_inventory_item"]),
    ("one_purchase_order_line", ROW_MEANING_LABELS["one_purchase_order_line"]),
    ("one_sales_order_line", ROW_MEANING_LABELS["one_sales_order_line"]),
    ("one_job_operation", ROW_MEANING_LABELS["one_job_operation"]),
    ("one_timecard_punch", ROW_MEANING_LABELS["one_timecard_punch"]),
]


@dataclass
class RowMeaningOption:
    value: str
    label: str

    def to_dict(self) -> dict:
        return {"value": self.value, "label": self.label}


@dataclass
class RowMeaning:
    inferred: str | None
    confidence: float
    evidence: list[str] = field(default_factory=list)
    options: list[RowMeaningOption] = field(default_factory=list)
    user_confirmed: str | None = None

    def to_dict(self) -> dict:
        effective = self.user_confirmed or self.inferred
        return {
            "inferred": self.inferred,
            "inferred_label": ROW_MEANING_LABELS.get(self.inferred or "", self.inferred or ""),
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
            "options": [o.to_dict() for o in self.options],
            "user_confirmed": self.user_confirmed,
            "effective": effective,
            "effective_label": ROW_MEANING_LABELS.get(effective or "", effective or ""),
        }

    def needs_confirmation(self, threshold: float = 0.75) -> bool:
        if self.user_confirmed:
            return False
        return self.confidence < threshold or self.inferred == "unknown"


def infer_row_meaning(classification: DatasetClassification) -> RowMeaning:
    likely: LikelyType = classification.likely_type
    inferred, confidence, evidence = _TYPE_TO_ROW_MEANING.get(
        likely, ("unknown", 0.2, ["No row meaning mapping for this classification"])
    )
    options = [RowMeaningOption(value=v, label=lbl) for v, lbl in ROW_MEANING_OPTIONS]
    return RowMeaning(
        inferred=inferred,
        confidence=confidence,
        evidence=list(evidence),
        options=options,
    )
