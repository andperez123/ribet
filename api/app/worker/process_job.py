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
from app.services.telemetry import track_stage
from app.services.pipeline_stage import set_job_pipeline_stage
from app.services.analysis import run_operational_analysis
from app.services.job_errors import (
    JobError,
    format_traceback,
    from_exception,
    org_not_found,
    scrub_detail_for_log,
    sector_disabled,
    unknown_report_type,
)

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


def _fail_job(db, job: IngestJob, err: JobError | str) -> None:
    if isinstance(err, str):
        from app.services.job_errors import normalize_stored_error

        normalized = normalize_stored_error(err)
        job_error = JobError(
            code=normalized["code"] or "processing_failed",
            message=normalized["message"] or err,
            hint=normalized.get("hint"),
            detail=normalized.get("detail"),
        )
    else:
        job_error = err

    payload = job_error.to_dict()
    job.status = "error"
    job.errors = [payload]
    emit_event(
        db,
        "job_failed",
        org_id=job.org_id,
        job_id=job.id,
        metadata={
            "file_name": job.file_name,
            "error_code": job_error.code,
            "error_message": job_error.message,
            "error_detail": scrub_detail_for_log(job_error.detail),
            "intake_metadata": job.intake_metadata,
        },
    )
    db.commit()
    logger.error(
        "job_failed org_id=%s job_id=%s file_name=%s code=%s message=%s detail=%s",
        job.org_id,
        job.id,
        job.file_name,
        job_error.code,
        job_error.message,
        job_error.detail,
    )


def process_job(db, job: IngestJob) -> None:
    org = db.get(Organization, job.org_id)
    if not org:
        _fail_job(db, job, org_not_found())
        return

    try:
        if job.sector in ("orders", "sales"):
            _fail_job(db, job, sector_disabled(job.sector))
            return

        with track_stage(
            db,
            "transform",
            org_id=org.id,
            job_id=job.id,
            extra={"file_name": job.file_name},
        ):
            set_job_pipeline_stage(db, job, "transform")
            result = transform_upload(db, org, job, job.file_name, job.storage_key)
        job.report_type = result.report_type
        db.commit()

        if result.status == "needs_review":
            set_job_pipeline_stage(db, job, "needs_review")
            emit_event(
                db,
                "job_needs_review",
                org_id=org.id,
                job_id=job.id,
                metadata={
                    "report_type": result.report_type,
                    "mapping_confidence": job.mapping_confidence,
                },
            )
            db.commit()
            logger.info(
                "job_needs_review org_id=%s job_id=%s confidence=%s",
                org.id,
                job.id,
                job.mapping_confidence,
            )
            return

        if result.row_count == 0 and result.report_type == "unknown":
            columns: list[str] = []
            if job.mapping_metadata and isinstance(job.mapping_metadata, dict):
                columns = list(job.mapping_metadata.get("source_columns") or [])
            _fail_job(
                db,
                job,
                unknown_report_type(filename=job.file_name, columns=columns),
            )
            return

        with track_stage(
            db,
            "analysis",
            org_id=org.id,
            job_id=job.id,
            extra={"report_type": result.report_type, "row_count": result.row_count},
        ):
            set_job_pipeline_stage(db, job, "rules")
            db.commit()
            analysis = run_operational_analysis(db, org.id, job.id, period=result.period)
        report = analysis.report
        job.report_id = report.id
        job.status = "done"
        set_job_pipeline_stage(db, job, "report_ready")
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        emit_event(
            db,
            "job_done",
            org_id=org.id,
            job_id=job.id,
            report_id=report.id,
            metadata={"report_type": result.report_type},
        )
        db.commit()
        try:
            from app.services.email import send_report_ready_email

            send_report_ready_email(db, org.id, report.id)
        except Exception as mail_err:
            logger.warning(
                "report_ready_email_failed org_id=%s report_id=%s error=%s",
                org.id,
                report.id,
                mail_err,
            )
        logger.info(
            "job_done org_id=%s job_id=%s report_id=%s report_type=%s",
            org.id,
            job.id,
            report.id,
            result.report_type,
        )
    except Exception as e:
        job_error = from_exception(e, filename=job.file_name)
        if not job_error.detail:
            job_error.detail = format_traceback(e)
        logger.exception(
            "job_exception org_id=%s job_id=%s file_name=%s",
            job.org_id,
            job.id,
            job.file_name,
        )
        _fail_job(db, job, job_error)


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
    from app.db_init import initialize_database

    initialize_database()
    _start_email_scheduler()
    last_purge = 0.0
    while True:
        db = SessionLocal()
        try:
            import time as _time

            now = _time.time()
            if now - last_purge > 3600:
                try:
                    from app.services.demo import purge_old_demo_orgs

                    n = purge_old_demo_orgs(db)
                    if n:
                        logger.info("demo_orgs_purged count=%s", n)
                except Exception as exc:
                    logger.warning("demo_purge_failed error=%s", exc)
                    db.rollback()
                last_purge = now

            job = claim_job(db)
            if job:
                emit_event(
                    db,
                    "job_claimed",
                    org_id=job.org_id,
                    job_id=job.id,
                    metadata={"file_name": job.file_name, "sector": job.sector},
                )
                db.commit()
                logger.info(
                    "job_claimed org_id=%s job_id=%s file_name=%s",
                    job.org_id,
                    job.id,
                    job.file_name,
                )
                process_job(db, job)
                from app.services.worker_status import touch_worker_heartbeat

                touch_worker_heartbeat(db)
            else:
                from app.services.worker_status import touch_worker_heartbeat

                touch_worker_heartbeat(db)
                time.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.exception("worker_error error=%s", e)
            db.rollback()
            time.sleep(POLL_INTERVAL)
        finally:
            db.close()


if __name__ == "__main__":
    run_worker()
