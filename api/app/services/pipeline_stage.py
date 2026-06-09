from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import IngestJob


def set_job_pipeline_stage(db: Session, job: IngestJob | None, stage: str) -> None:
    if job is None:
        return
    job.pipeline_stage = stage
    db.flush()
