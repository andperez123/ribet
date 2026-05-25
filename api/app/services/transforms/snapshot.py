from __future__ import annotations

"""Build operational snapshots from persisted domain data."""

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import GlTransaction, InventoryItem, Invoice, OperationalSnapshot, Vendor
from app.services.transforms.canonical.models import OperationalSnapshotData


def get_prior_snapshot(
    db: Session, org_id: UUID, exclude_period: str | None = None
) -> OperationalSnapshot | None:
    q = db.query(OperationalSnapshot).filter(OperationalSnapshot.org_id == org_id)
    if exclude_period:
        q = q.filter(OperationalSnapshot.period != exclude_period)
    return q.order_by(OperationalSnapshot.computed_at.desc()).first()


def build_operational_snapshot(
    db: Session,
    org_id: UUID,
    period: str,
    job_id: UUID,
    health_score: int,
    health_status: str,
) -> OperationalSnapshot:
    ar_total = (
        db.query(func.sum(Invoice.amount)).filter(Invoice.org_id == org_id).scalar() or 0
    )
    over_90 = (
        db.query(func.sum(Invoice.amount))
        .filter(Invoice.org_id == org_id, Invoice.days_overdue >= 90)
        .scalar()
        or 0
    )
    ar_over_90_pct = (over_90 / ar_total * 100) if ar_total > 0 else 0.0

    ap_total = (
        db.query(func.sum(Vendor.balance))
        .filter(Vendor.org_id == org_id, Vendor.balance > 0)
        .scalar()
        or 0
    )
    vendors = db.query(Vendor).filter(Vendor.org_id == org_id, Vendor.balance > 0).all()
    vendor_concentration = 0.0
    if vendors and ap_total > 0:
        top = max(vendors, key=lambda v: v.balance or 0)
        vendor_concentration = ((top.balance or 0) / ap_total) * 100

    inventory_value = (
        db.query(func.sum(InventoryItem.quantity))
        .filter(InventoryItem.org_id == org_id)
        .scalar()
        or 0
    )

    adj_keywords = ["adjustment", "adj", "write-off", "shrinkage"]
    gl_rows = db.query(GlTransaction).filter(GlTransaction.org_id == org_id).all()
    adj_total = sum(
        abs(r.amount)
        for r in gl_rows
        if any(kw in (r.account_name or r.account_id or "").lower() for kw in adj_keywords)
    )

    data = OperationalSnapshotData(
        period=period,
        ar_over_90_pct=round(ar_over_90_pct, 2),
        ar_total=float(ar_total),
        ap_total=float(ap_total),
        inventory_value=float(inventory_value),
        inventory_turns=None,
        vendor_concentration=round(vendor_concentration, 2),
        health_score=health_score,
        health_status=health_status,
        metrics={"inventory_adjustment_total": adj_total},
    )

    existing = (
        db.query(OperationalSnapshot)
        .filter(OperationalSnapshot.org_id == org_id, OperationalSnapshot.period == period)
        .first()
    )
    if existing:
        snap = existing
    else:
        snap = OperationalSnapshot(org_id=org_id, period=period)
        db.add(snap)

    snap.cash_position = None
    snap.ar_over_90_pct = data.ar_over_90_pct
    snap.ar_total = data.ar_total
    snap.ap_total = data.ap_total
    snap.inventory_value = data.inventory_value
    snap.inventory_turns = data.inventory_turns
    snap.vendor_concentration = data.vendor_concentration
    snap.health_score = data.health_score
    snap.health_status = data.health_status
    snap.metrics = data.metrics
    jid = str(job_id)
    job_ids = [str(x) for x in (snap.source_job_ids or [])]
    if jid not in job_ids:
        job_ids.append(jid)
    snap.source_job_ids = job_ids
    db.flush()
    return snap


def snapshot_delta_strings(
    current: OperationalSnapshot,
    prior: OperationalSnapshot | None,
) -> list[str]:
    if not prior:
        return []
    deltas: list[str] = []
    if current.ar_over_90_pct is not None and prior.ar_over_90_pct is not None:
        d = current.ar_over_90_pct - prior.ar_over_90_pct
        if abs(d) >= 1:
            deltas.append(
                f"AR over 90 days: {prior.ar_over_90_pct:.1f}% → {current.ar_over_90_pct:.1f}% "
                f"({'+' if d > 0 else ''}{d:.1f}pp)"
            )
    if current.health_score and prior.health_score:
        d = current.health_score - prior.health_score
        if abs(d) >= 3:
            deltas.append(
                f"Health score: {prior.health_score} → {current.health_score} ({'+' if d > 0 else ''}{d})"
            )
    if (
        current.vendor_concentration is not None
        and prior.vendor_concentration is not None
    ):
        d = current.vendor_concentration - prior.vendor_concentration
        if abs(d) >= 5:
            deltas.append(
                f"Vendor concentration: {prior.vendor_concentration:.1f}% → "
                f"{current.vendor_concentration:.1f}%"
            )
    return deltas
