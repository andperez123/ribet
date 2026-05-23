from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_organization, verify_api_key
from app.models import HealthSnapshot, Organization
from app.schemas import HealthHistory, HealthScore

router = APIRouter(prefix="/v1/health", tags=["health"])


@router.get("/score", response_model=HealthScore)
def get_health_score(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    snap = (
        db.query(HealthSnapshot)
        .filter(HealthSnapshot.org_id == org.id)
        .order_by(HealthSnapshot.computed_at.desc())
        .first()
    )
    if not snap:
        return HealthScore(score=0, status="Unknown", components={})
    return HealthScore(
        score=snap.score,
        status=snap.status,
        components=snap.components or {},
        computed_at=snap.computed_at.isoformat() if snap.computed_at else None,
    )


@router.get("/history", response_model=HealthHistory)
def get_health_history(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
    limit: int = 12,
):
    snaps = (
        db.query(HealthSnapshot)
        .filter(HealthSnapshot.org_id == org.id)
        .order_by(HealthSnapshot.computed_at.desc())
        .limit(limit)
        .all()
    )
    return HealthHistory(
        snapshots=[
            HealthScore(
                score=s.score,
                status=s.status,
                components=s.components or {},
                computed_at=s.computed_at.isoformat() if s.computed_at else None,
            )
            for s in snaps
        ]
    )
