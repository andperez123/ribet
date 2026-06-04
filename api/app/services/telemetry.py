from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.events import emit_event


@contextmanager
def track_stage(
    db: Session,
    stage: str,
    *,
    org_id: UUID | None = None,
    job_id: UUID | None = None,
    report_id: UUID | None = None,
    extra: dict | None = None,
) -> Iterator[None]:
    """Emit {stage}_started / _completed / _failed with duration_ms."""
    base_meta = {"stage": stage, **(extra or {})}
    emit_event(
        db,
        f"{stage}_started",
        org_id=org_id,
        job_id=job_id,
        report_id=report_id,
        metadata=base_meta,
    )
    db.commit()

    start = time.perf_counter()
    err: BaseException | None = None
    try:
        yield
    except BaseException as e:
        err = e
        raise
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)
        meta = {**base_meta, "duration_ms": duration_ms}
        if err is not None:
            meta["error_type"] = type(err).__name__
            meta["error"] = str(err)[:500]
            db.rollback()
            emit_event(
                db,
                f"{stage}_failed",
                org_id=org_id,
                job_id=job_id,
                report_id=report_id,
                metadata=meta,
            )
        else:
            emit_event(
                db,
                f"{stage}_completed",
                org_id=org_id,
                job_id=job_id,
                report_id=report_id,
                metadata=meta,
            )
        db.commit()
