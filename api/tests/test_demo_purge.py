from datetime import datetime, timedelta, timezone

from app.models import IngestJob, Organization
from app.seed import DEMO_ORG_ID
from app.services.demo import purge_old_demo_orgs


def test_purge_old_demo_orgs_deletes_jobs(client):
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        org = Organization(name="Demo abc123", erp_family="jobboss")
        db.add(org)
        db.flush()
        org.created_at = datetime.now(timezone.utc) - timedelta(hours=48)
        db.add(
            IngestJob(
                org_id=org.id,
                file_name="ap_aging_jobboss.csv",
                mime_type="text/csv",
                storage_key=f"{org.id}/test.csv",
                status="done",
            )
        )
        db.commit()

        deleted = purge_old_demo_orgs(db, max_age_hours=24)
        assert deleted == 1
        assert db.get(Organization, org.id) is None
        assert db.query(IngestJob).filter(IngestJob.org_id == org.id).count() == 0
    finally:
        db.close()
