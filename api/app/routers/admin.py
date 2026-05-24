from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import verify_admin_key
from app.schemas.metrics import AdminMetricsOut
from app.services.metrics import compute_admin_metrics

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/metrics", response_model=AdminMetricsOut)
def get_admin_metrics(
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key),
):
    return compute_admin_metrics(db)
