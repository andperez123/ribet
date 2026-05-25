from __future__ import annotations

"""Background worker — polls ingest_jobs and runs ETL + rules + report."""

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import text

from app.database import SessionLocal
from app.models import IngestJob, Organization
from app.services.transforms.pipeline import transform_upload
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
        if job.sector in ("orders", "sales"):
            _fail_job(
                db,
                job,
                f"Sector '{job.sector}' is not enabled yet. Upload financials or manufacturing exports.",
            )
            return

        result = transform_upload(db, org, job.id, job.file_name, job.storage_key)
        job.report_type = result.report_type
        db.commit()

        if result.row_count == 0 and result.report_type == "unknown":
            _fail_job(db, job, "Could not detect report type or parse file")
            return

        report = generate_report(db, org.id, [job.id], period=result.period)
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
            result.report_type,
        )
    except Exception as e:
        _fail_job(db, job, str(e))


def _start_email_scheduler():
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        from app.database import SessionLocal
        from app.services.email import send_briefs_for_active_orgs

        def _job():
            db = SessionLocal()
            try:
                send_briefs_for_active_orgs(db)
            finally:
                db.close()

        sched = BackgroundScheduler()
        sched.add_job(_job, "cron", day_of_week="mon", hour=8, minute=0)
        sched.start()
        logger.info("email_scheduler_started")
    except Exception as e:
        logger.warning("email_scheduler_failed error=%s", e)


def run_worker():
    logger.info("worker_started")
    _start_email_scheduler()
    last_purge = 0.0
    while True:
        db = SessionLocal()
        try:
            import time as _time

            now = _time.time()
            if now - last_purge > 3600:
                from app.services.demo import purge_old_demo_orgs

                n = purge_old_demo_orgs(db)
                if n:
                    logger.info("demo_orgs_purged count=%s", n)
                last_purge = now

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
