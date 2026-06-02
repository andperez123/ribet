from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_organization, verify_api_key
from app.models import Organization
from pydantic import BaseModel, Field

from app.schemas import DataGapOut, DemoOrgResponse, OrgCoverageOut, OrgProgressOut, UploadJob
from app.services.demo import create_demo_organization
from app.services.org_coverage import build_org_coverage_payload
from app.services.progress import get_org_progress

router = APIRouter(prefix="/v1/org", tags=["org"])


def _job_to_schema(job) -> UploadJob:
    return UploadJob(
        id=job.id,
        status=job.status,  # type: ignore
        file_name=job.file_name,
        sector=job.sector,
        errors=job.errors or [],
        report_id=job.report_id,
        created_at=job.created_at.isoformat() if job.created_at else None,
        updated_at=job.updated_at.isoformat() if job.updated_at else None,
    )


@router.post("/demo", response_model=DemoOrgResponse)
def create_demo(db: Session = Depends(get_db)):
    """Public endpoint — creates ephemeral org and queues fixture uploads."""
    org, jobs = create_demo_organization(db)
    return DemoOrgResponse(
        org_id=org.id,
        org_name=org.name,
        jobs=[_job_to_schema(j) for j in jobs],
    )


@router.get("/progress", response_model=OrgProgressOut)
def org_progress(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    data = get_org_progress(db, org.id)
    return OrgProgressOut(**data)


@router.get("/coverage", response_model=OrgCoverageOut)
def org_coverage(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    data = build_org_coverage_payload(db, org.id)
    return OrgCoverageOut(**data)


@router.get("/gaps", response_model=list[DataGapOut])
def org_gaps(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    data = build_org_coverage_payload(db, org.id)
    return [DataGapOut(**g) for g in data["gaps"]]


class OrgSettingsOut(BaseModel):
    email_recipients: list[str] = Field(default_factory=list)


class OrgSettingsUpdate(BaseModel):
    email_recipients: list[str] = Field(default_factory=list)


@router.get("/settings", response_model=OrgSettingsOut)
def get_org_settings(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    db.refresh(org)
    return OrgSettingsOut(email_recipients=list(org.email_recipients or []))


@router.patch("/settings", response_model=OrgSettingsOut)
def update_org_settings(
    body: OrgSettingsUpdate,
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    org.email_recipients = body.email_recipients
    db.commit()
    db.refresh(org)
    return OrgSettingsOut(email_recipients=list(org.email_recipients or []))


class ClerkOrgCreate(BaseModel):
    clerk_org_id: str
    name: str


@router.post("/from-clerk")
def create_from_clerk(
    body: ClerkOrgCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    from app.models import Organization as OrgModel

    existing = (
        db.query(OrgModel).filter(OrgModel.clerk_org_id == body.clerk_org_id).first()
    )
    if existing:
        return {"org_id": str(existing.id), "created": False}
    org = OrgModel(name=body.name, clerk_org_id=body.clerk_org_id, erp_family="jobboss")
    db.add(org)
    db.commit()
    db.refresh(org)
    return {"org_id": str(org.id), "created": True}
