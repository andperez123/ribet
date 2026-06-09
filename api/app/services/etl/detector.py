"""Detect report type from filename, column headers, and upload sector hint."""

from __future__ import annotations

REPORT_SIGNATURES = {
    "ar_aging": ["customer", "aging", "overdue", "days", "balance"],
    "ap_aging": ["vendor", "aging", "balance", "payable"],
    "gl_detail": ["account", "gl", "debit", "credit", "journal", "amount"],
    "inventory": ["sku", "item", "quantity", "qty", "on hand", "inventory"],
    "purchase_orders": ["purchase order", "po number", "po #", "po no", "promise date", "receipt"],
    "sales_orders": ["sales order", "so number", "ship date", "order qty", "backorder"],
}

_SECTOR_HINTS: dict[str, list[str]] = {
    "financials": ["ar_aging", "ap_aging", "gl_detail"],
    "manufacturing": ["inventory", "work_orders"],
    "orders": ["purchase_orders", "ap_aging"],
    "sales": ["sales_orders", "ar_aging"],
}


def detect_report_type(
    filename: str,
    columns: list[str],
    sector_hint: str | None = None,
) -> str:
    name_lower = filename.lower()
    cols_lower = " ".join(str(c).lower() for c in columns)

    if "ar" in name_lower and "aging" in name_lower:
        return "ar_aging"
    if "ap" in name_lower and "aging" in name_lower:
        return "ap_aging"
    if "purchase" in name_lower and "order" in name_lower:
        return "purchase_orders"
    if "sales" in name_lower and "order" in name_lower:
        return "sales_orders"
    if "gl" in name_lower or "journal" in name_lower:
        return "gl_detail"
    if "inventory" in name_lower or "inv" in name_lower:
        return "inventory"

    scores: dict[str, float] = {}
    for report_type, keywords in REPORT_SIGNATURES.items():
        scores[report_type] = float(sum(1 for kw in keywords if kw in cols_lower))

    if sector_hint and sector_hint in _SECTOR_HINTS:
        for report_type in _SECTOR_HINTS[sector_hint]:
            scores[report_type] = scores.get(report_type, 0) + 0.5

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"
