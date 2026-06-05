"""End-to-end pipeline test with fixtures."""

import io
from pathlib import Path

from app.models import Organization
from app.seed import DEMO_ORG_ID
from app.worker.process_job import process_job

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def test_full_pipeline_ar_aging(client):
    from app.database import SessionLocal
    from app.models import IngestJob, OperationalReport
    from app.services.storage import upload_file

    db = SessionLocal()
    org = Organization(id=DEMO_ORG_ID, name="Test", erp_family="jobboss")
    db.merge(org)
    db.commit()

    content = (FIXTURES / "ar_aging_jobboss.csv").read_bytes()
    job = IngestJob(
        org_id=DEMO_ORG_ID,
        file_name="ar_aging_jobboss.csv",
        storage_key="",
        status="pending",
        errors=[],
    )
    db.add(job)
    db.flush()
    job.storage_key = upload_file(DEMO_ORG_ID, job.id, job.file_name, content)
    db.commit()

    process_job(db, job)

    db.refresh(job)
    assert job.status == "done"
    assert job.report_id is not None

    report = db.get(OperationalReport, job.report_id)
    assert report is not None
    assert report.health_score >= 0
    assert len(report.executive_summary) > 0
    assert report.data_digest is not None
    assert report.data_coverage is not None
    assert report.data_coverage.get("ar") is True
    assert len(report.domain_insights or []) > 0
    assert report.analysis_metadata is not None

    db.close()
