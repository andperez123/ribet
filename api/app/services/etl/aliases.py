"""Column alias normalization — maps ERP-specific headers to canonical names."""

from __future__ import annotations

import re

COLUMN_ALIASES: dict[str, list[str]] = {
    "customer_id": ["customer id", "cust id", "customer_number", "customer no", "client", "cust#"],
    "customer_name": ["customer name", "customer", "name", "client name"],
    "vendor_id": ["vendor id", "vendor no", "vendor_number", "vendor#", "supplier id"],
    "vendor_name": ["vendor name", "vendor", "supplier", "supplier name"],
    "invoice_id": ["invoice", "invoice no", "invoice number", "inv no", "document"],
    "amount": [
        "amount",
        "balance",
        "open balance",
        "open amount",
        "total balance",
        "total",
        "total owed",
        "total open",
        "open ($)",
        "invoice amount",
        "amount due",
        "balance due",
        "open ar",
        "ar balance",
        "customer total",
        "vendor total",
    ],
    "days_overdue": ["days overdue", "days past due", "age days", "overdue days"],
    "aging_bucket": ["aging bucket", "bucket", "aging", "age category"],
    "account_id": ["account", "account id", "gl account", "acct", "account no", "account number"],
    "account_name": ["account name", "description", "account description"],
    "posted_at": ["date", "posting date", "posted", "transaction date", "trans date"],
    "sku": ["sku", "part number", "part no", "item", "item number", "part#"],
    "item_id": ["item id", "item no", "inventory id", "part id"],
    "quantity": ["quantity", "qty", "on hand", "onhand", "qty on hand"],
    "gl_account": ["gl account", "inventory account", "acct"],
}

MONETARY_TOKENS = frozenset(
    {"amount", "balance", "total", "open", "due", "receivable", "payable", "owed", "ar", "ap"}
)
ENTITY_TOKENS = frozenset({"customer", "client", "vendor", "supplier", "cust", "name"})

# Aging bucket column headers (not mapped to canonical fields — used for sum_buckets strategy)
_DAYS_SUFFIX = r"(?:\s*days?)?"
AGING_BUCKET_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(rf"^current(?:\s*\([^)]*\))?{_DAYS_SUFFIX}$", re.I), 0),
    (re.compile(rf"^(?:0[\s-]*30|1[\s-]*30|0-30|1-30){_DAYS_SUFFIX}(?:\s*\([^)]*\))?$", re.I), 15),
    (re.compile(rf"^(?:31[\s-]*60|30[\s-]*60|31-60){_DAYS_SUFFIX}$", re.I), 45),
    (re.compile(rf"^(?:61[\s-]*90|60[\s-]*90|61-90){_DAYS_SUFFIX}$", re.I), 75),
    (re.compile(rf"^(?:91[\s-]*120|90[\s-]*120|91-120){_DAYS_SUFFIX}$", re.I), 105),
    (re.compile(rf"^(?:over\s*90|90\+|91\+|>\s*90){_DAYS_SUFFIX}$", re.I), 95),
    (re.compile(rf"^(?:over\s*120|120\+|>\s*120){_DAYS_SUFFIX}$", re.I), 125),
    (re.compile(rf"^90[\s-]*180{_DAYS_SUFFIX}$", re.I), 135),
    (re.compile(rf"^(?:180\+|over\s*180){_DAYS_SUFFIX}$", re.I), 200),
]

BUCKET_CANONICAL_KEYS = ("current", "1_30", "31_60", "61_90", "91_plus", "over_120")


def bucket_canonical_key(col: str, implied_days: int) -> str:
    """Map a bucket column header to a stable breakdown key."""
    lower = str(col).lower().strip()
    if "current" in lower or implied_days == 0:
        return "current"
    if implied_days <= 30:
        return "1_30"
    if implied_days <= 60:
        return "31_60"
    if implied_days <= 90:
        return "61_90"
    if implied_days <= 120:
        return "91_plus"
    return "over_120"


def _tokenize(header: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", header.lower()))


def _is_monetary_header(header: str) -> bool:
    lower = header.lower().strip()
    tokens = _tokenize(header)
    if tokens & MONETARY_TOKENS:
        return True
    return any(tok in lower for tok in ("balance", "total", "amount", " open ", " due "))


def _is_entity_name_header(header: str) -> bool:
    lower = header.lower().strip()
    tokens = _tokenize(header)
    if not (tokens & ENTITY_TOKENS):
        return False
    if _is_monetary_header(header):
        return False
    return True


def _score_column(header: str, canonical: str, aliases: list[str]) -> float:
    lower = header.lower().strip()
    if not lower:
        return 0.0

    best = 0.0
    for alias in aliases:
        if lower == alias:
            best = max(best, 1.0)
        elif lower.startswith(alias + " ") or lower.endswith(" " + alias):
            best = max(best, 0.85)
        elif alias in lower and len(alias) >= 4:
            best = max(best, 0.65)
        elif lower in alias and len(lower) >= 4:
            best = max(best, 0.55)

    if best == 0.0:
        return 0.0

    if canonical == "amount":
        if _is_monetary_header(header):
            best = min(1.0, best + 0.25)
        if _is_entity_name_header(header) and not _is_monetary_header(header):
            best *= 0.3
    elif canonical in ("customer_name", "customer_id", "vendor_name", "vendor_id"):
        if _is_monetary_header(header):
            best *= 0.1
        elif _is_entity_name_header(header):
            best = min(1.0, best + 0.15)
        vendor_tokens = _tokenize(header) & frozenset({"vendor", "supplier"})
        customer_tokens = _tokenize(header) & frozenset({"customer", "client", "cust"})
        if canonical in ("customer_name", "customer_id") and vendor_tokens:
            best *= 0.05
        elif canonical in ("customer_name", "customer_id") and customer_tokens:
            best = min(1.0, best + 0.2)
        elif canonical in ("vendor_name", "vendor_id") and customer_tokens:
            best *= 0.05
        elif canonical in ("vendor_name", "vendor_id") and vendor_tokens:
            best = min(1.0, best + 0.2)

    if canonical == "customer_name" and "total" in lower and "customer" in lower:
        best *= 0.05
    if canonical == "vendor_name" and "total" in lower and "vendor" in lower:
        best *= 0.05

    return best


def detect_aging_bucket_columns(columns: list[str]) -> list[tuple[str, int]]:
    """Return (original_column_name, implied_days_overdue) for aging bucket cols."""
    buckets: list[tuple[str, int]] = []
    for col in columns:
        normalized = str(col).lower().strip()
        for pattern, days in AGING_BUCKET_PATTERNS:
            if pattern.search(normalized):
                buckets.append((col, days))
                break
    return buckets


def normalize_columns(columns: list[str]) -> dict[str, str]:
    """Map original column names to canonical field names using scored matching."""
    if not columns:
        return {}

    bucket_cols = {c for c, _ in detect_aging_bucket_columns([str(c) for c in columns])}

    scores: list[tuple[float, str, str]] = []
    for col in columns:
        if str(col) in bucket_cols:
            continue
        for canonical, aliases in COLUMN_ALIASES.items():
            score = _score_column(str(col), canonical, aliases)
            if score >= 0.5:
                scores.append((score, col, canonical))

    scores.sort(key=lambda x: x[0], reverse=True)

    mapping: dict[str, str] = {}
    used_cols: set[str] = set()
    used_canonical: set[str] = set()

    for score, col, canonical in scores:
        if col in used_cols or canonical in used_canonical:
            continue
        mapping[col] = canonical
        used_cols.add(col)
        used_canonical.add(canonical)

    return mapping


def rename_dataframe(df, column_map: dict[str, str]):
    return df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
