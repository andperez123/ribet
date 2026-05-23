from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_organization, verify_api_key
from app.models import IngestJob, Organization
from app.schemas import UploadJob, UploadJobsResponse
from app.services.ingest import create_upload_jobs

router = APIRouter(prefix="/v1/ingest", tags=["ingest"])


def _job_to_schema(job: IngestJob) -> UploadJob:
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


@router.post("/uploads", response_model=UploadJobsResponse)
async def upload_files(
    files: list[UploadFile] = File(...),
    sector: str | None = Form(None),
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    try:
        jobs = await create_upload_jobs(
            db, org, files, settings.max_upload_bytes, sector=sector
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return UploadJobsResponse(jobs=[_job_to_schema(j) for j in jobs])


@router.get("/jobs", response_model=UploadJobsResponse)
def list_jobs(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
    limit: int = 20,
):
    jobs = (
        db.query(IngestJob)
        .filter(IngestJob.org_id == org.id)
        .order_by(IngestJob.created_at.desc())
        .limit(limit)
        .all()
    )
    return UploadJobsResponse(jobs=[_job_to_schema(j) for j in jobs])


@router.get("/jobs/{job_id}", response_model=UploadJob)
def get_job(
    job_id: UUID,
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    job = db.get(IngestJob, job_id)
    if not job or job.org_id != org.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_schema(job)
