from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas import JobErrorOut


class JobFailureOut(BaseModel):
    event_id: UUID
    created_at: str
    org_id: UUID | None = None
    org_name: str | None = None
    job_id: UUID | None = None
    file_name: str | None = None
    sector: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    error_detail: str | None = None
    intake_metadata: dict | None = None
    job_errors: list[JobErrorOut] = Field(default_factory=list)
    job_status: str | None = None


class JobFailuresResponse(BaseModel):
    failures: list[JobFailureOut]
    total: int
