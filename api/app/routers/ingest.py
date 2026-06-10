from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_organization, verify_api_key
from app.models import IngestJob, Organization
from app.schemas import JobErrorOut, UploadJob, UploadJobsResponse
from app.services.ingest import create_upload_jobs
from app.services.job_errors import normalize_stored_error
from app.services.mapping_review import confirm_job_mapping, get_mapping_review

router = APIRouter(prefix="/v1/ingest", tags=["ingest"])


def _job_to_schema(job: IngestJob) -> UploadJob:
    return UploadJob(
        id=job.id,
        status=job.status,  # type: ignore
        file_name=job.file_name,
        sector=job.sector,
        errors=[
            JobErrorOut(**normalize_stored_error(err))
            for err in (job.errors or [])
        ],
        report_id=job.report_id,
        mapping_status=job.mapping_status,
        mapping_confidence=job.mapping_confidence,
        duplicate_of_job_id=job.duplicate_of_job_id,
        created_at=job.created_at.isoformat() if job.created_at else None,
        updated_at=job.updated_at.isoformat() if job.updated_at else None,
        intake_metadata=job.intake_metadata if job.status == "error" else None,
        pipeline_stage=job.pipeline_stage,
    )


@router.post("/uploads", response_model=UploadJobsResponse)
async def upload_files(
    files: list[UploadFile] = File(...),
    sector: str | None = Form(None),
    consent_acknowledged: str = Form("false"),
    description: str | None = Form(None),
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    if consent_acknowledged.lower() not in ("true", "1", "on", "yes"):
        raise HTTPException(
            status_code=400,
            detail="Upload consent required",
        )
    try:
        jobs = await create_upload_jobs(
            db,
            org,
            files,
            settings.max_upload_bytes,
            sector=sector,
            consent_acknowledged=True,
            description=description,
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


@router.get("/jobs/{job_id}/mapping")
def get_job_mapping(
    job_id: UUID,
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    job = db.get(IngestJob, job_id)
    if not job or job.org_id != org.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return get_mapping_review(db, job)


class MappingConfirmRequest(BaseModel):
    column_map: dict[str, str] = Field(default_factory=dict)
    amount_strategy: str | None = None
    mapping_answers: dict[str, str] = Field(default_factory=dict)
    row_meaning: str | None = None
    apply_schema_memory: bool | None = None


@router.post("/jobs/{job_id}/mapping/confirm", response_model=UploadJob)
def confirm_mapping(
    job_id: UUID,
    body: MappingConfirmRequest,
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    job = db.get(IngestJob, job_id)
    if not job or job.org_id != org.id:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "needs_review":
        raise HTTPException(status_code=400, detail="Job is not awaiting mapping review")
    try:
        job = confirm_job_mapping(
            db,
            org,
            job,
            column_map=body.column_map or None,
            amount_strategy=body.amount_strategy,
            mapping_answers=body.mapping_answers or None,
            row_meaning=body.row_meaning,
            apply_schema_memory=body.apply_schema_memory,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _job_to_schema(job)
