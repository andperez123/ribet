from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import verify_admin_key
from app.models import Organization
from app.schemas.metrics import AdminMetricsOut
from app.services.email import send_weekly_brief
from app.services.metrics import compute_admin_metrics

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/metrics", response_model=AdminMetricsOut)
def get_admin_metrics(
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key),
):
    return compute_admin_metrics(db)


@router.post("/brief/test")
def test_weekly_brief(
    org_id: UUID,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key),
):
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    ok = send_weekly_brief(db, org_id)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Brief not sent — check RESEND_API_KEY and email recipients",
        )
    return {"ok": True, "org_id": str(org_id)}
