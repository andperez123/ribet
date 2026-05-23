"""Detect report type from filename and column headers."""

REPORT_SIGNATURES = {
    "ar_aging": ["customer", "aging", "overdue", "days", "balance"],
    "ap_aging": ["vendor", "aging", "balance", "payable"],
    "gl_detail": ["account", "gl", "debit", "credit", "journal", "amount"],
    "inventory": ["sku", "item", "quantity", "qty", "on hand", "inventory"],
}


def detect_report_type(filename: str, columns: list[str]) -> str:
    name_lower = filename.lower()
    cols_lower = " ".join(str(c).lower() for c in columns)

    if "ar" in name_lower and "aging" in name_lower:
        return "ar_aging"
    if "ap" in name_lower and "aging" in name_lower:
        return "ap_aging"
    if "gl" in name_lower or "journal" in name_lower:
        return "gl_detail"
    if "inventory" in name_lower or "inv" in name_lower:
        return "inventory"

    scores = {}
    for report_type, keywords in REPORT_SIGNATURES.items():
        scores[report_type] = sum(1 for kw in keywords if kw in cols_lower)

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"
