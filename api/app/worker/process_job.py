"""Background worker — polls ingest_jobs and runs ETL + rules + report."""

import time
from datetime import datetime, timezone

from sqlalchemy import text

from app.database import SessionLocal
from app.models import IngestJob, Organization
from app.services.etl.pipeline import run_etl
from app.services.progress import recompute_org_progress
from app.services.report import generate_report

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


def process_job(db, job: IngestJob) -> None:
    org = db.get(Organization, job.org_id)
    if not org:
        job.status = "error"
        job.errors = ["Organization not found"]
        db.commit()
        return

    try:
        if job.file_name.lower().endswith(".pdf"):
            job.report_type = "pdf"
            job.status = "done"
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            recompute_org_progress(db, org.id)
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
                return
            job.errors = ["Could not detect report type or parse file"]
            job.status = "error"
            db.commit()
            return

        report = generate_report(db, org.id, [job.id])
        job.report_id = report.id
        job.status = "done"
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        recompute_org_progress(db, org.id)
    except Exception as e:
        job.status = "error"
        job.errors = [str(e)]
        db.commit()


def run_worker():
    from app.database import Base, engine

    Base.metadata.create_all(bind=engine)
    print("Ribet worker started")
    while True:
        db = SessionLocal()
        try:
            job = claim_job(db)
            if job:
                print(f"Processing job {job.id} ({job.file_name})")
                process_job(db, job)
            else:
                time.sleep(POLL_INTERVAL)
        except Exception as e:
            print(f"Worker error: {e}")
            db.rollback()
            time.sleep(POLL_INTERVAL)
        finally:
            db.close()


if __name__ == "__main__":
    run_worker()
