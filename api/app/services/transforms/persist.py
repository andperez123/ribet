"""Persist canonical records to existing ORM tables."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Customer, GlTransaction, InventoryItem, Invoice, Vendor
from app.services.transforms.canonical.models import CanonicalDataset


def persist_canonical(
    db: Session,
    org_id: UUID,
    job_id: UUID,
    period: str,
    dataset: CanonicalDataset,
) -> int:
    total = 0

    if dataset.ar:
        db.query(Invoice).filter(
            Invoice.org_id == org_id, Invoice.period_label == period
        ).delete(synchronize_session=False)
        seen_customers: set[str] = set()
        for rec in dataset.ar:
            if rec.customer_id not in seen_customers:
                existing = (
                    db.query(Customer)
                    .filter(
                        Customer.org_id == org_id,
                        Customer.customer_id == rec.customer_id,
                    )
                    .first()
                )
                if existing:
                    existing.name = rec.customer_name or rec.customer_id
                    existing.source_job_id = job_id
                else:
                    db.add(
                        Customer(
                            org_id=org_id,
                            customer_id=rec.customer_id,
                            name=rec.customer_name or rec.customer_id,
                            source_job_id=job_id,
                        )
                    )
                seen_customers.add(rec.customer_id)
            db.add(
                Invoice(
                    org_id=org_id,
                    invoice_id=rec.invoice_id,
                    customer_id=rec.customer_id,
                    amount=float(rec.amount),
                    due_date=rec.due_date.isoformat() if rec.due_date else "",
                    days_overdue=rec.days_overdue,
                    aging_bucket=rec.aging_bucket or "",
                    period_label=period,
                    source_job_id=job_id,
                )
            )
            total += 1

    if dataset.ap:
        db.query(Vendor).filter(
            Vendor.org_id == org_id, Vendor.period_label == period
        ).delete(synchronize_session=False)
        for rec in dataset.ap:
            db.add(
                Vendor(
                    org_id=org_id,
                    vendor_id=rec.vendor_id,
                    name=rec.vendor_name or rec.vendor_id,
                    balance=float(rec.balance),
                    period_label=period,
                    source_job_id=job_id,
                )
            )
            total += 1

    if dataset.gl:
        db.query(GlTransaction).filter(
            GlTransaction.org_id == org_id, GlTransaction.period_label == period
        ).delete(synchronize_session=False)
        for rec in dataset.gl:
            db.add(
                GlTransaction(
                    org_id=org_id,
                    transaction_id=rec.transaction_id,
                    account_id=rec.account_id,
                    account_name=rec.account_name,
                    amount=float(rec.amount),
                    posted_at=rec.posted_at,
                    period_label=period,
                    source_job_id=job_id,
                )
            )
            total += 1

    if dataset.inventory:
        db.query(InventoryItem).filter(
            InventoryItem.org_id == org_id, InventoryItem.period_label == period
        ).delete(synchronize_session=False)
        for rec in dataset.inventory:
            db.add(
                InventoryItem(
                    org_id=org_id,
                    item_id=rec.item_id,
                    sku=rec.sku,
                    quantity=float(rec.quantity),
                    gl_account=rec.gl_account,
                    period_label=period,
                    source_job_id=job_id,
                )
            )
            total += 1

    db.flush()
    return total
