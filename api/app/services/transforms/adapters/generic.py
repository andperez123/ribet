"""Generic adapter — maps normalized dataframes to canonical records."""

from __future__ import annotations

import re
from datetime import date
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
    CanonicalPurchaseOrder,
    CanonicalSalesOrder,
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


def _dec_optional(val) -> Decimal | None:
    if pd.isna(val) or not str(val).strip():
        return None
    try:
        return Decimal(str(val).replace(",", "").replace("$", ""))
    except Exception:
        return None


def _parse_date_str(val) -> str | None:
    if pd.isna(val) or not str(val).strip():
        return None
    try:
        return pd.to_datetime(val).date().isoformat()
    except Exception:
        return str(val).strip()[:32] or None


def _days_late(*date_vals) -> int:
    ref = date.today()
    best: date | None = None
    for val in date_vals:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            continue
        try:
            parsed = pd.to_datetime(val).date()
            if best is None or parsed < best:
                best = parsed
        except Exception:
            continue
    if best is None:
        return 0
    return max(0, (ref - best).days)


_OPEN_STATUS = re.compile(r"open|partial|released|pending|active|backorder|outstanding", re.I)
_CLOSED_STATUS = re.compile(r"closed|complete|completed|received|shipped|cancel", re.I)


def _is_open_status(status: str, open_amount: Decimal) -> bool:
    s = (status or "").strip()
    if s and _CLOSED_STATUS.search(s):
        return False
    if open_amount > 0:
        return True
    if s and _OPEN_STATUS.search(s):
        return True
    return open_amount > 0


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

    elif report_type == "purchase_orders":
        for i, row in df.iterrows():
            po_id = _safe_str(row.get("po_id", f"PO-{i}"))
            vendor = _safe_str(row.get("vendor_name", row.get("vendor_id", "")))
            if not po_id or not vendor or not _valid_entity(vendor):
                continue
            open_amt = _dec(row.get("open_amount", row.get("amount", 0)))
            line_amt = _dec(row.get("line_amount", row.get("amount", open_amt)))
            if open_amt <= 0:
                open_amt = line_amt
            status = _safe_str(row.get("status", ""))
            if not _is_open_status(status, open_amt):
                continue
            promise = row.get("promise_date") or row.get("due_date")
            days_late = _days_late(promise, row.get("due_date"))
            if days_late <= 0 and _dec(row.get("days_overdue", 0)) > 0:
                days_late = int(_dec(row.get("days_overdue", 0)))
            dataset.purchase_orders.append(
                CanonicalPurchaseOrder(
                    po_id=po_id,
                    vendor_id=_safe_str(row.get("vendor_id", vendor)) or vendor,
                    vendor_name=vendor,
                    order_date=_parse_date_str(row.get("order_date")),
                    promise_date=_parse_date_str(promise),
                    due_date=_parse_date_str(row.get("due_date")),
                    status=status or None,
                    line_amount=line_amt,
                    open_amount=open_amt,
                    days_late=days_late,
                    sku=_safe_str(row.get("sku", "")) or None,
                    qty_ordered=_dec_optional(row.get("qty_ordered")),
                    qty_received=_dec_optional(row.get("qty_received")),
                )
            )

    elif report_type == "sales_orders":
        for i, row in df.iterrows():
            order_id = _safe_str(row.get("order_id", f"SO-{i}"))
            customer = _safe_str(row.get("customer_name", row.get("customer_id", "")))
            if not order_id or not customer or not _valid_entity(customer):
                continue
            open_amt = _dec(row.get("open_amount", row.get("amount", 0)))
            line_amt = _dec(row.get("line_amount", row.get("amount", open_amt)))
            if open_amt <= 0:
                open_amt = line_amt
            status = _safe_str(row.get("status", ""))
            if not _is_open_status(status, open_amt):
                continue
            ship_target = row.get("ship_date") or row.get("promise_date")
            days_late = _days_late(ship_target, row.get("promise_date"))
            if days_late <= 0 and _dec(row.get("days_overdue", 0)) > 0:
                days_late = int(_dec(row.get("days_overdue", 0)))
            dataset.sales_orders.append(
                CanonicalSalesOrder(
                    order_id=order_id,
                    customer_id=_safe_str(row.get("customer_id", customer)) or customer,
                    customer_name=customer,
                    order_date=_parse_date_str(row.get("order_date")),
                    ship_date=_parse_date_str(row.get("ship_date")),
                    promise_date=_parse_date_str(row.get("promise_date")),
                    status=status or None,
                    line_amount=line_amt,
                    open_amount=open_amt,
                    days_late=days_late,
                    sku=_safe_str(row.get("sku", "")) or None,
                    qty_ordered=_dec_optional(row.get("qty_ordered")),
                    qty_open=_dec_optional(row.get("qty_open", row.get("quantity"))),
                )
            )

    return dataset
