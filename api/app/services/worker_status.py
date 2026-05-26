from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import IngestJob, ProductEvent


def touch_worker_heartbeat(db: Session, min_interval_seconds: int = 60) -> None:
    from app.services.events import emit_event

    last = (
        db.query(func.max(ProductEvent.created_at))
        .filter(ProductEvent.event_type == "worker_heartbeat")
        .scalar()
    )
    now = datetime.now(timezone.utc)
    if last:
        last_utc = last if last.tzinfo else last.replace(tzinfo=timezone.utc)
        if (now - last_utc).total_seconds() < min_interval_seconds:
            return
    emit_event(db, "worker_heartbeat")
    db.commit()


def get_worker_status(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    pending = (
        db.query(func.count(IngestJob.id))
        .filter(IngestJob.status == "pending")
        .scalar()
        or 0
    )
    processing = (
        db.query(func.count(IngestJob.id))
        .filter(IngestJob.status == "processing")
        .scalar()
        or 0
    )
    last_done = (
        db.query(func.max(IngestJob.updated_at))
        .filter(IngestJob.status == "done")
        .scalar()
    )
    last_heartbeat = (
        db.query(func.max(ProductEvent.created_at))
        .filter(ProductEvent.event_type == "worker_heartbeat")
        .scalar()
    )
    last_job_done_event = (
        db.query(func.max(ProductEvent.created_at))
        .filter(ProductEvent.event_type.in_(("job_done", "job_failed")))
        .scalar()
    )

    heartbeat_fresh = False
    if last_heartbeat:
        hb = last_heartbeat if last_heartbeat.tzinfo else last_heartbeat.replace(tzinfo=timezone.utc)
        heartbeat_fresh = (now - hb) < timedelta(minutes=5)

    worker_alive = heartbeat_fresh or processing > 0
    if not worker_alive and pending > 0 and last_done:
        done_at = last_done if last_done.tzinfo else last_done.replace(tzinfo=timezone.utc)
        worker_alive = (now - done_at) < timedelta(minutes=10)

    return {
        "ok": True,
        "worker_alive": worker_alive,
        "pending_jobs": pending,
        "processing_jobs": processing,
        "last_job_completed_at": last_done.isoformat() if last_done else None,
        "last_heartbeat_at": last_heartbeat.isoformat() if last_heartbeat else None,
        "last_job_event_at": last_job_done_event.isoformat() if last_job_done_event else None,
    }
