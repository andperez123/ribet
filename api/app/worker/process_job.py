"""Background worker — polls ingest_jobs and runs ETL + rules + report."""

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import text

from app.database import SessionLocal
from app.models import IngestJob, Organization
from app.services.etl.pipeline import run_etl
from app.services.events import emit_event
from app.services.progress import recompute_org_progress
from app.services.report import generate_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s event=%(message)s",
)
logger = logging.getLogger("ribet.worker")

POLL_INTERVAL = 2


def claim_job(db) -> IngestJob | None:
    row = db.execute(
        text(
            """
            UPDATE ingest_jobs
            SET status = 'processing', updated_at = NOW()
            WHERE id = (
                SELECT id FROM ingest_jobs
                WHERE status = 'pending'
                ORDER BY created_at
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id
            """
        )
    ).fetchone()
    if not row:
        return None
    db.commit()
    return db.get(IngestJob, row[0])


def _fail_job(db, job: IngestJob, message: str) -> None:
    job.status = "error"
    job.errors = [message]
    emit_event(
        db,
        "job_failed",
        org_id=job.org_id,
        job_id=job.id,
        metadata={"error": message, "file_name": job.file_name},
    )
    db.commit()
    logger.info(
        "job_failed org_id=%s job_id=%s file_name=%s error=%s",
        job.org_id,
        job.id,
        job.file_name,
        message,
    )


def process_job(db, job: IngestJob) -> None:
    org = db.get(Organization, job.org_id)
    if not org:
        _fail_job(db, job, "Organization not found")
        return

    try:
        if job.file_name.lower().endswith(".pdf"):
            job.report_type = "pdf"
            job.status = "done"
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            recompute_org_progress(db, org.id)
            logger.info(
                "job_done org_id=%s job_id=%s report_type=pdf report_id=",
                org.id,
                job.id,
            )
            return

        report_type, row_count = run_etl(db, org, job.id, job.file_name, job.storage_key)
        job.report_type = report_type
        db.commit()

        if row_count == 0 and report_type == "unknown":
            if job.sector in ("orders", "sales"):
                job.status = "done"
                job.updated_at = datetime.now(timezone.utc)
                db.commit()
                recompute_org_progress(db, org.id)
                logger.info(
                    "job_done org_id=%s job_id=%s report_type=unknown sector=%s",
                    org.id,
                    job.id,
                    job.sector,
                )
                return
            _fail_job(db, job, "Could not detect report type or parse file")
            return

        report = generate_report(db, org.id, [job.id])
        job.report_id = report.id
        job.status = "done"
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        recompute_org_progress(db, org.id)
        logger.info(
            "job_done org_id=%s job_id=%s report_id=%s report_type=%s",
            org.id,
            job.id,
            report.id,
            report_type,
        )
    except Exception as e:
        _fail_job(db, job, str(e))


def run_worker():
    from app.database import Base, engine

    Base.metadata.create_all(bind=engine)
    logger.info("worker_started")
    while True:
        db = SessionLocal()
        try:
            job = claim_job(db)
            if job:
                logger.info(
                    "job_claimed org_id=%s job_id=%s file_name=%s",
                    job.org_id,
                    job.id,
                    job.file_name,
                )
                process_job(db, job)
            else:
                time.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.exception("worker_error error=%s", e)
            db.rollback()
            time.sleep(POLL_INTERVAL)
        finally:
            db.close()


if __name__ == "__main__":
    run_worker()
