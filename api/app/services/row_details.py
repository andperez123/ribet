"""Row-level operational context for evidence pack and chat."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Customer, InventoryItem, Invoice, PurchaseOrder, SalesOrder, Vendor


def build_row_details(
    db: Session,
    org_id: UUID,
    period: str,
    source_job_ids: list[UUID] | None = None,
    extra_column_samples: dict[str, list[str]] | None = None,
) -> dict:
    """Aggregate row-level facts the LLM can cite by name and document ID."""

    def _job_filter(model, q):
        if source_job_ids:
            q = q.filter(model.source_job_id.in_(source_job_ids))
        return q.filter(model.period_label == period)

    ar_overdue: list[dict] = []
    inv_q = _job_filter(
        Invoice,
        db.query(Invoice, Customer.name)
        .outerjoin(
            Customer,
            (Customer.customer_id == Invoice.customer_id)
            & (Customer.org_id == Invoice.org_id),
        )
        .filter(Invoice.org_id == org_id),
    )
    for inv, cust_name in inv_q.order_by(Invoice.amount.desc()).limit(200).all():
        days = inv.days_overdue or 0
        if days < 30 and (inv.aging_bucket or "").lower() not in ("61-90", "91+", "over 90"):
            continue
        ar_overdue.append(
            {
                "customer": cust_name or inv.customer_id,
                "invoice_id": inv.invoice_id,
                "amount": float(inv.amount or 0),
                "days_overdue": days,
                "aging_bucket": inv.aging_bucket,
                "due_date": inv.due_date,
            }
        )
    ar_overdue.sort(key=lambda r: r["amount"], reverse=True)
    ar_overdue = ar_overdue[:25]

    ap_late: list[dict] = []
    ven_q = _job_filter(
        Vendor,
        db.query(Vendor).filter(Vendor.org_id == org_id),
    )
    for ven in ven_q.order_by(Vendor.balance.desc()).limit(200).all():
        days = ven.days_overdue or 0
        balance = float(ven.balance or 0)
        if balance <= 0 and days < 30:
            continue
        if days < 30 and balance > 0 and not ven.aging_bucket:
            continue
        ap_late.append(
            {
                "vendor": ven.name or ven.vendor_id,
                "vendor_id": ven.vendor_id,
                "balance": balance,
                "days_overdue": days,
                "aging_bucket": ven.aging_bucket,
            }
        )
    ap_late.sort(key=lambda r: r["balance"], reverse=True)
    ap_late = ap_late[:25]

    inventory_issues: list[dict] = []
    item_q = _job_filter(
        InventoryItem,
        db.query(InventoryItem).filter(InventoryItem.org_id == org_id),
    )
    for item in item_q.limit(500).all():
        qty = float(item.quantity or 0)
        if qty >= 0 and item.gl_account:
            continue
        inventory_issues.append(
            {
                "sku": item.sku or item.item_id,
                "quantity": qty,
                "gl_account": item.gl_account,
                "issue": "negative_qty" if qty < 0 else "missing_gl_account",
            }
        )
    inventory_issues.sort(key=lambda r: abs(r["quantity"]), reverse=True)
    inventory_issues = inventory_issues[:25]

    late_pos: list[dict] = []
    po_q = _job_filter(
        PurchaseOrder,
        db.query(PurchaseOrder).filter(
            PurchaseOrder.org_id == org_id,
            PurchaseOrder.days_late >= 7,
            PurchaseOrder.open_amount > 0,
        ),
    )
    for po in po_q.order_by(PurchaseOrder.open_amount.desc()).limit(25).all():
        late_pos.append(
            {
                "po_id": po.po_id,
                "vendor": po.vendor_name or po.vendor_id,
                "vendor_id": po.vendor_id,
                "open_amount": float(po.open_amount or 0),
                "days_late": po.days_late or 0,
                "promise_date": po.promise_date,
                "sku": po.sku,
                "status": po.status,
            }
        )

    past_due_sos: list[dict] = []
    so_q = _job_filter(
        SalesOrder,
        db.query(SalesOrder).filter(
            SalesOrder.org_id == org_id,
            SalesOrder.days_late >= 1,
            SalesOrder.open_amount > 0,
        ),
    )
    for so in so_q.order_by(SalesOrder.open_amount.desc()).limit(25).all():
        past_due_sos.append(
            {
                "order_id": so.order_id,
                "customer": so.customer_name or so.customer_id,
                "customer_id": so.customer_id,
                "open_amount": float(so.open_amount or 0),
                "days_late": so.days_late or 0,
                "ship_date": so.ship_date,
                "promise_date": so.promise_date,
                "sku": so.sku,
                "status": so.status,
            }
        )

    return {
        "ar_overdue_accounts": ar_overdue,
        "ap_late_vendors": ap_late,
        "inventory_issues": inventory_issues,
        "late_purchase_orders": late_pos,
        "past_due_sales_orders": past_due_sos,
        "extra_column_samples": extra_column_samples or {},
    }
