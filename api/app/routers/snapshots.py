from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_organization, verify_api_key
from app.models import OperationalSnapshot, Organization

router = APIRouter(prefix="/v1/snapshots", tags=["snapshots"])


class SnapshotOut(BaseModel):
    period: str
    health_score: int
    health_status: str
    ar_over_90_pct: float | None
    ar_total: float | None
    ap_total: float | None
    inventory_value: float | None
    vendor_concentration: float | None
    computed_at: str


class SnapshotHistoryOut(BaseModel):
    snapshots: list[SnapshotOut]


def _to_out(s: OperationalSnapshot) -> SnapshotOut:
    return SnapshotOut(
        period=s.period,
        health_score=s.health_score,
        health_status=s.health_status,
        ar_over_90_pct=s.ar_over_90_pct,
        ar_total=s.ar_total,
        ap_total=s.ap_total,
        inventory_value=s.inventory_value,
        vendor_concentration=s.vendor_concentration,
        computed_at=s.computed_at.isoformat() if s.computed_at else "",
    )


@router.get("/latest", response_model=SnapshotOut)
def latest_snapshot(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    snap = (
        db.query(OperationalSnapshot)
        .filter(OperationalSnapshot.org_id == org.id)
        .order_by(OperationalSnapshot.computed_at.desc())
        .first()
    )
    if not snap:
        raise HTTPException(status_code=404, detail="No snapshots yet")
    return _to_out(snap)


@router.get("/history", response_model=SnapshotHistoryOut)
def snapshot_history(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
    limit: int = 12,
):
    snaps = (
        db.query(OperationalSnapshot)
        .filter(OperationalSnapshot.org_id == org.id)
        .order_by(OperationalSnapshot.computed_at.desc())
        .limit(limit)
        .all()
    )
    return SnapshotHistoryOut(snapshots=[_to_out(s) for s in snaps])
