from __future__ import annotations

"""Generic fallback parser using column aliases."""

from datetime import datetime, timezone
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Customer, GlTransaction, InventoryItem, Invoice, Vendor
from app.services.etl.aliases import normalize_columns, rename_dataframe


def _period_from_df(df: pd.DataFrame, fallback: str | None = None) -> str:
    for col in ("posting_date", "due_date", "posted_at"):
        if col in df.columns:
            dates = pd.to_datetime(df[col], errors="coerce").dropna()
            if len(dates):
                return dates.max().strftime("%Y-%m")
    return fallback or datetime.now(timezone.utc).strftime("%Y-%m")


def _safe_str(val) -> str:
    if pd.isna(val):
        return ""
    return str(val).strip()


def _safe_float(val) -> float:
    try:
        if pd.isna(val):
            return 0.0
        return float(str(val).replace(",", "").replace("$", ""))
    except (ValueError, TypeError):
        return 0.0


def parse_ar_aging(db: Session, org_id: UUID, job_id: UUID, df: pd.DataFrame) -> int:
    col_map = normalize_columns(list(df.columns))
    df = rename_dataframe(df, col_map)
    period = _period_from_df(df)
    db.query(Invoice).filter(
        Invoice.org_id == org_id, Invoice.period_label == period
    ).delete(synchronize_session=False)
    count = 0
    customers_seen: set[str] = set()

    for _, row in df.iterrows():
        cust_id = _safe_str(row.get("customer_id", row.get("customer_name", "")))
        if not cust_id:
            continue
        if cust_id not in customers_seen:
            existing = (
                db.query(Customer)
                .filter(Customer.org_id == org_id, Customer.customer_id == cust_id)
                .first()
            )
            name = _safe_str(row.get("customer_name", cust_id))
            if existing:
                existing.name = name
                existing.source_job_id = job_id
            else:
                db.add(
                    Customer(
                        org_id=org_id,
                        customer_id=cust_id,
                        name=name,
                        source_job_id=job_id,
                    )
                )
            customers_seen.add(cust_id)
        inv_id = _safe_str(row.get("invoice_id", f"{cust_id}-{count}"))
        db.add(
            Invoice(
                org_id=org_id,
                invoice_id=inv_id,
                customer_id=cust_id,
                amount=_safe_float(row.get("amount", 0)),
                due_date=_safe_str(row.get("due_date", "")),
                days_overdue=int(_safe_float(row.get("days_overdue", 0))),
                aging_bucket=_safe_str(row.get("aging_bucket", "")),
                period_label=period,
                source_job_id=job_id,
            )
        )
        count += 1
    return count


def parse_ap_aging(db: Session, org_id: UUID, job_id: UUID, df: pd.DataFrame) -> int:
    col_map = normalize_columns(list(df.columns))
    df = rename_dataframe(df, col_map)
    period = _period_from_df(df)
    db.query(Vendor).filter(
        Vendor.org_id == org_id, Vendor.period_label == period
    ).delete(synchronize_session=False)
    count = 0
    for _, row in df.iterrows():
        vid = _safe_str(row.get("vendor_id", row.get("vendor_name", "")))
        if not vid:
            continue
        db.add(
            Vendor(
                org_id=org_id,
                vendor_id=vid,
                name=_safe_str(row.get("vendor_name", vid)),
                balance=_safe_float(row.get("amount", 0)),
                period_label=period,
                source_job_id=job_id,
            )
        )
        count += 1
    return count


def parse_gl_detail(db: Session, org_id: UUID, job_id: UUID, df: pd.DataFrame) -> int:
    col_map = normalize_columns(list(df.columns))
    df = rename_dataframe(df, col_map)
    period = _period_from_df(df)
    db.query(GlTransaction).filter(
        GlTransaction.org_id == org_id, GlTransaction.period_label == period
    ).delete(synchronize_session=False)
    count = 0
    for i, row in df.iterrows():
        acct = _safe_str(row.get("account_id", ""))
        if not acct:
            continue
        db.add(
            GlTransaction(
                org_id=org_id,
                transaction_id=f"{job_id}-{i}",
                account_id=acct,
                account_name=_safe_str(row.get("account_name", "")),
                amount=_safe_float(row.get("amount", 0)),
                posted_at=_safe_str(row.get("posted_at", "")),
                period_label=period,
                source_job_id=job_id,
            )
        )
        count += 1
    return count


def parse_inventory(db: Session, org_id: UUID, job_id: UUID, df: pd.DataFrame) -> int:
    col_map = normalize_columns(list(df.columns))
    df = rename_dataframe(df, col_map)
    period = _period_from_df(df)
    db.query(InventoryItem).filter(
        InventoryItem.org_id == org_id, InventoryItem.period_label == period
    ).delete(synchronize_session=False)
    count = 0
    for i, row in df.iterrows():
        sku = _safe_str(row.get("sku", row.get("item_id", f"item-{i}")))
        if not sku:
            continue
        db.add(
            InventoryItem(
                org_id=org_id,
                item_id=sku,
                sku=sku,
                quantity=_safe_float(row.get("quantity", 0)),
                gl_account=_safe_str(row.get("gl_account", "")),
                period_label=period,
                source_job_id=job_id,
            )
        )
        count += 1
    return count


PARSERS = {
    "ar_aging": parse_ar_aging,
    "ap_aging": parse_ap_aging,
    "gl_detail": parse_gl_detail,
    "inventory": parse_inventory,
}
