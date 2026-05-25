from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ProductEvent


def emit_event(
    db: Session,
    event_type: str,
    org_id: UUID | None = None,
    job_id: UUID | None = None,
    report_id: UUID | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(
        ProductEvent(
            event_type=event_type,
            org_id=org_id,
            job_id=job_id,
            report_id=report_id,
            metadata_=metadata or {},
        )
    )
