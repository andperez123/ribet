"""Generic adapter — maps normalized dataframes to canonical records."""

from decimal import Decimal

import pandas as pd

from app.services.etl.aliases import normalize_columns, rename_dataframe
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


def dataframe_to_canonical(report_type: str, df: pd.DataFrame) -> CanonicalDataset:
    col_map = normalize_columns(list(df.columns))
    df = rename_dataframe(df, col_map)
    dataset = CanonicalDataset()

    if report_type == "ar_aging":
        for i, row in df.iterrows():
            cust = _safe_str(row.get("customer_id", row.get("customer_name", "")))
            if not cust:
                continue
            dataset.ar.append(
                CanonicalARRecord(
                    customer_id=cust,
                    customer_name=_safe_str(row.get("customer_name", cust)) or None,
                    invoice_id=_safe_str(row.get("invoice_id", f"{cust}-{i}")),
                    amount=_dec(row.get("amount", 0)),
                    days_overdue=int(float(_dec(row.get("days_overdue", 0)))),
                    aging_bucket=_safe_str(row.get("aging_bucket", "")) or None,
                )
            )
    elif report_type == "ap_aging":
        for _, row in df.iterrows():
            vid = _safe_str(row.get("vendor_id", row.get("vendor_name", "")))
            if not vid:
                continue
            dataset.ap.append(
                CanonicalAPRecord(
                    vendor_id=vid,
                    vendor_name=_safe_str(row.get("vendor_name", vid)) or None,
                    balance=_dec(row.get("amount", 0)),
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
