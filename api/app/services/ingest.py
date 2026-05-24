import mimetypes
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import IngestJob, Organization
from app.services.events import emit_event
from app.services.sectors import validate_sector
from app.services.storage import upload_file

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf"}


def validate_file(filename: str, content: bytes, max_bytes: int) -> None:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type not allowed: {ext}")
    if len(content) > max_bytes:
        raise ValueError(f"File exceeds max size of {max_bytes} bytes")


async def create_upload_jobs(
    db: Session,
    org: Organization,
    files: list[UploadFile],
    max_bytes: int,
    sector: str | None = None,
) -> list[IngestJob]:
    validated_sector = validate_sector(sector)
    jobs: list[IngestJob] = []
    for upload in files:
        content = await upload.read()
        filename = upload.filename or "unknown"
        validate_file(filename, content, max_bytes)

        job = IngestJob(
            org_id=org.id,
            file_name=filename,
            mime_type=upload.content_type or mimetypes.guess_type(filename)[0],
            storage_key="",
            status="pending",
            errors=[],
            sector=validated_sector,
        )
        db.add(job)
        db.flush()

        key = upload_file(org.id, job.id, filename, content)
        job.storage_key = key
        emit_event(
            db,
            "file_uploaded",
            org_id=org.id,
            job_id=job.id,
            metadata={"file_name": filename, "sector": validated_sector},
        )
        jobs.append(job)

    db.commit()
    for j in jobs:
        db.refresh(j)
    return jobs
