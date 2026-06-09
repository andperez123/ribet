"""Admin view of recent ingest job failures."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import IngestJob, Organization, ProductEvent
from app.schemas import JobErrorOut
from app.schemas.admin import JobFailureOut, JobFailuresResponse
from app.services.job_errors import normalize_stored_error


def list_job_failures(db: Session, *, limit: int = 50) -> JobFailuresResponse:
    limit = max(1, min(limit, 200))
    events = (
        db.query(ProductEvent)
        .filter(ProductEvent.event_type == "job_failed")
        .order_by(ProductEvent.created_at.desc())
        .limit(limit)
        .all()
    )

    org_ids = {e.org_id for e in events if e.org_id}
    job_ids = {e.job_id for e in events if e.job_id}

    orgs: dict[UUID, Organization] = {}
    if org_ids:
        orgs = {
            o.id: o
            for o in db.query(Organization).filter(Organization.id.in_(org_ids)).all()
        }

    jobs: dict[UUID, IngestJob] = {}
    if job_ids:
        jobs = {
            j.id: j
            for j in db.query(IngestJob).filter(IngestJob.id.in_(job_ids)).all()
        }

    failures: list[JobFailureOut] = []
    for event in events:
        meta = event.metadata_ or {}
        job = jobs.get(event.job_id) if event.job_id else None
        org = orgs.get(event.org_id) if event.org_id else None

        job_errors = [
            normalize_stored_error(err, include_detail=True)
            for err in (job.errors or [])
        ] if job else []

        primary = job_errors[0] if job_errors else None
        error_code = meta.get("error_code") or (primary or {}).get("code")
        error_message = meta.get("error_message") or (primary or {}).get("message")
        error_detail = meta.get("error_detail") or (primary or {}).get("detail")

        failures.append(
            JobFailureOut(
                event_id=event.id,
                created_at=event.created_at.isoformat() if event.created_at else "",
                org_id=event.org_id,
                org_name=org.name if org else None,
                job_id=event.job_id,
                file_name=meta.get("file_name") or (job.file_name if job else None),
                sector=job.sector if job else None,
                error_code=str(error_code) if error_code else None,
                error_message=str(error_message) if error_message else None,
                error_detail=str(error_detail) if error_detail else None,
                intake_metadata=(
                    job.intake_metadata
                    if job and job.intake_metadata
                    else meta.get("intake_metadata")
                ),
                job_errors=[JobErrorOut(**err) for err in job_errors],
                job_status=job.status if job else None,
            )
        )

    return JobFailuresResponse(failures=failures, total=len(failures))
