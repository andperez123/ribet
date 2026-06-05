"""Generic adapter — maps normalized dataframes to canonical records."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd

from app.services.etl.aliases import detect_aging_bucket_columns, normalize_columns, rename_dataframe
from app.services.transforms.canonical.models import (
    CanonicalAPRecord,
    CanonicalARRecord,
    CanonicalDataset,
    CanonicalGLTransaction,
    CanonicalInventoryItem,
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


def _sum_bucket_amounts(row, bucket_cols: list[tuple[str, int]]) -> tuple[Decimal, int, str]:
    total = Decimal("0")
    max_days = 0
    dominant_bucket = ""
    for col, days in bucket_cols:
        amt = _dec(row.get(col, 0))
        if amt > 0:
            total += amt
            if days >= max_days:
                max_days = days
                dominant_bucket = str(col)
    return total, max_days, dominant_bucket


def _resolve_ar_amount(row, bucket_cols: list[tuple[str, int]]) -> tuple[Decimal, int, str | None]:
    amount = _dec(row.get("amount", 0))
    if amount > 0:
        days = int(float(_dec(row.get("days_overdue", 0))))
        bucket = _safe_str(row.get("aging_bucket", "")) or None
        return amount, days, bucket

    if bucket_cols:
        total, days, bucket = _sum_bucket_amounts(row, bucket_cols)
        if total > 0:
            return total, days, bucket or None

    return amount, int(float(_dec(row.get("days_overdue", 0)))), _safe_str(row.get("aging_bucket", "")) or None


def _looks_like_currency_label(value: str) -> bool:
    stripped = value.replace(",", "").replace("$", "").strip()
    if not stripped:
        return False
    try:
        float(stripped)
        return "$" in value or "," in value or "." in stripped
    except ValueError:
        return False


def dataframe_to_canonical(report_type: str, df: pd.DataFrame) -> CanonicalDataset:
    original_columns = list(df.columns)
    col_map = normalize_columns(original_columns)
    df = rename_dataframe(df, col_map)
    bucket_cols = detect_aging_bucket_columns(original_columns)
    dataset = CanonicalDataset()

    if report_type == "ar_aging":
        for i, row in df.iterrows():
            cust = _safe_str(row.get("customer_id", row.get("customer_name", "")))
            cust_name = _safe_str(row.get("customer_name", cust)) or None
            if cust_name and _looks_like_currency_label(cust_name):
                if cust and not _looks_like_currency_label(cust):
                    cust_name = cust
                else:
                    cust_name = None
            if not cust and cust_name:
                cust = cust_name
            if not cust:
                continue
            if _looks_like_currency_label(cust):
                continue

            amount, days_overdue, aging_bucket = _resolve_ar_amount(row, bucket_cols)
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
        for _, row in df.iterrows():
            vid = _safe_str(row.get("vendor_id", row.get("vendor_name", "")))
            if not vid or _looks_like_currency_label(vid):
                continue
            amount, _, _ = _resolve_ar_amount(row, bucket_cols)
            dataset.ap.append(
                CanonicalAPRecord(
                    vendor_id=vid,
                    vendor_name=_safe_str(row.get("vendor_name", vid)) or None,
                    balance=amount,
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
