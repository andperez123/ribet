"""Generic adapter — maps normalized dataframes to canonical records."""

from __future__ import annotations

import re
from decimal import Decimal

import pandas as pd

from app.services.etl.aliases import (
    bucket_canonical_key,
    detect_aging_bucket_columns,
    normalize_columns,
    rename_dataframe,
)
from app.services.etl.field_mapper import MappingPlan
from app.services.transforms.canonical.models import (
    CanonicalAPRecord,
    CanonicalARRecord,
    CanonicalDataset,
    CanonicalGLTransaction,
    CanonicalInventoryItem,
)

_SUMMARY_ROW_PATTERNS = re.compile(
    r"^(?:total\s+open|grand\s+total|total|subtotal|summary)(?:\s*\([^)]*\))?$",
    re.I,
)


def _safe_str(val) -> str:
    if pd.isna(val):
        return ""
    return str(val).strip()


def _dec(val) -> Decimal:
    try:
        if pd.isna(val):
            return Decimal("0")
        return Decimal(str(val).replace(",", "").replace("$", ""))
    except Exception:
        return Decimal("0")


def _sum_bucket_amounts(
    row,
    bucket_cols: list[tuple[str, int]],
    source_row=None,
) -> tuple[Decimal, int, str, dict[str, float]]:
    bucket_row = source_row if source_row is not None else row
    total = Decimal("0")
    max_days = 0
    dominant_bucket = ""
    breakdown: dict[str, float] = {}
    for col, days in bucket_cols:
        amt = _dec(bucket_row.get(col, 0))
        if amt > 0:
            total += amt
            key = bucket_canonical_key(col, days)
            breakdown[key] = breakdown.get(key, 0.0) + float(amt)
            if days >= max_days:
                max_days = days
                dominant_bucket = str(col)
    return total, max_days, dominant_bucket, breakdown


def _resolve_ar_amount(
    row,
    bucket_cols: list[tuple[str, int]],
    source_row=None,
) -> tuple[Decimal, int, str | None, dict[str, float]]:
    amount = _dec(row.get("amount", 0))
    if amount > 0:
        days = int(float(_dec(row.get("days_overdue", 0))))
        bucket = _safe_str(row.get("aging_bucket", "")) or None
        breakdown: dict[str, float] = {}
        if bucket_cols:
            _, _, _, breakdown = _sum_bucket_amounts(row, bucket_cols, source_row)
        return amount, days, bucket, breakdown

    if bucket_cols:
        total, days, bucket, breakdown = _sum_bucket_amounts(row, bucket_cols, source_row)
        if total > 0:
            return total, days, bucket or None, breakdown

    return (
        amount,
        int(float(_dec(row.get("days_overdue", 0)))),
        _safe_str(row.get("aging_bucket", "")) or None,
        {},
    )


def _looks_like_currency_label(value: str) -> bool:
    stripped = value.replace(",", "").replace("$", "").strip()
    if not stripped:
        return False
    try:
        float(stripped)
        return "$" in value or "," in value or "." in stripped
    except ValueError:
        return False


def _looks_like_numeric_entity(value: str) -> bool:
    stripped = value.replace(",", "").replace("$", "").strip()
    if not stripped or re.search(r"[a-zA-Z]", stripped):
        return False
    digits = re.sub(r"[^\d]", "", stripped)
    return len(digits) >= 4


def _is_summary_entity(value: str) -> bool:
    return bool(_SUMMARY_ROW_PATTERNS.match(value.strip()))


def _valid_entity(value: str) -> bool:
    if not value:
        return False
    if _is_summary_entity(value):
        return False
    if _looks_like_currency_label(value):
        return False
    if _looks_like_numeric_entity(value):
        return False
    return True


def dataframe_to_canonical(
    report_type: str,
    df: pd.DataFrame,
    plan: MappingPlan | None = None,
) -> CanonicalDataset:
    original_columns = list(df.columns)
    source_df = df
    col_map = plan.column_map if plan else normalize_columns(original_columns)
    df = rename_dataframe(df, col_map)
    bucket_cols = detect_aging_bucket_columns(original_columns)
    dataset = CanonicalDataset()

    if report_type == "ar_aging":
        for i, row in df.iterrows():
            source_row = source_df.loc[i]
            cust = _safe_str(row.get("customer_id", row.get("customer_name", "")))
            cust_name = _safe_str(row.get("customer_name", cust)) or None
            if cust_name and not _valid_entity(cust_name):
                if cust and _valid_entity(cust):
                    cust_name = cust
                else:
                    cust_name = None
            if not cust and cust_name:
                cust = cust_name
            if not cust or not _valid_entity(cust):
                continue
            if cust_name and not _valid_entity(cust_name):
                cust_name = cust

            amount, days_overdue, aging_bucket, _ = _resolve_ar_amount(row, bucket_cols, source_row)
            if amount <= 0 and bucket_cols:
                _, _, _, breakdown = _sum_bucket_amounts(row, bucket_cols, source_row)
                if not breakdown:
                    continue
            dataset.ar.append(
                CanonicalARRecord(
                    customer_id=cust,
                    customer_name=cust_name,
                    invoice_id=_safe_str(row.get("invoice_id", f"{cust}-{i}")),
                    amount=amount,
                    days_overdue=days_overdue,
                    aging_bucket=aging_bucket,
                )
            )
    elif report_type == "ap_aging":
        for i, row in df.iterrows():
            source_row = source_df.loc[i]
            vid = _safe_str(row.get("vendor_id", row.get("vendor_name", "")))
            vname = _safe_str(row.get("vendor_name", vid)) or None
            if not vid or not _valid_entity(vid):
                continue
            if vname and not _valid_entity(vname):
                vname = vid if _valid_entity(vid) else None

            amount, days_overdue, aging_bucket, breakdown = _resolve_ar_amount(row, bucket_cols, source_row)
            if amount <= 0 and bucket_cols:
                _, days_overdue, aging_bucket, breakdown = _sum_bucket_amounts(row, bucket_cols, source_row)
            if amount <= 0 and not breakdown:
                continue

            bucket_total = Decimal(str(sum(breakdown.values()))) if breakdown else Decimal("0")

            dataset.ap.append(
                CanonicalAPRecord(
                    vendor_id=vid,
                    vendor_name=vname,
                    balance=amount if amount > 0 else bucket_total,
                    days_overdue=days_overdue,
                    aging_bucket=aging_bucket,
                    bucket_breakdown=breakdown,
                )
            )
    elif report_type == "gl_detail":
        for i, row in df.iterrows():
            acct = _safe_str(row.get("account_id", ""))
            if not acct:
                continue
            dataset.gl.append(
                CanonicalGLTransaction(
                    transaction_id=f"gl-{i}",
                    account_id=acct,
                    account_name=_safe_str(row.get("account_name", "")) or None,
                    amount=_dec(row.get("amount", 0)),
                    posted_at=_safe_str(row.get("posted_at", "")) or None,
                )
            )
    elif report_type == "inventory":
        for i, row in df.iterrows():
            sku = _safe_str(row.get("sku", row.get("item_id", f"item-{i}")))
            if not sku:
                continue
            dataset.inventory.append(
                CanonicalInventoryItem(
                    item_id=sku,
                    sku=sku,
                    quantity=_dec(row.get("quantity", 0)),
                    gl_account=_safe_str(row.get("gl_account", "")) or None,
                )
            )

    return dataset
