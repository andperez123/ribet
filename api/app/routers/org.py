from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_organization, verify_api_key
from app.models import Organization
from app.schemas import OrgProgressOut
from app.services.progress import get_org_progress

router = APIRouter(prefix="/v1/org", tags=["org"])


@router.get("/progress", response_model=OrgProgressOut)
def org_progress(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    data = get_org_progress(db, org.id)
    return OrgProgressOut(**data)
