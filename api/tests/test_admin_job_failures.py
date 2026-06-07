"""Admin job failures API tests."""

from app.models import Organization, ProductEvent
from app.seed import DEMO_ORG_ID

ADMIN_KEY = "dev-admin-secret"
ADMIN_HEADERS = {"X-Admin-Key": ADMIN_KEY}


def _seed_org(db):
    if not db.get(Organization, DEMO_ORG_ID):
        db.add(
            Organization(
                id=DEMO_ORG_ID,
                name="Demo Manufacturing Co",
                erp_family="jobboss",
            )
        )
        db.commit()


def test_admin_job_failures_requires_key(client):
    r = client.get("/v1/admin/job-failures")
    assert r.status_code == 401


def test_admin_job_failures_returns_events(client):
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        _seed_org(db)
        db.add(
            ProductEvent(
                event_type="job_failed",
                org_id=DEMO_ORG_ID,
                metadata_={
                    "file_name": "broken.xlsx",
                    "error_code": "excel_read_failed",
                    "error_message": "We couldn't read this Excel file.",
                    "error_detail": "BadZipFile: not a zip",
                },
            )
        )
        db.commit()
    finally:
        db.close()

    r = client.get("/v1/admin/job-failures", headers=ADMIN_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "failures" in data
    assert data["total"] >= 1
    row = data["failures"][0]
    assert row["error_code"] == "excel_read_failed"
    assert row["file_name"] == "broken.xlsx"
    assert row["org_name"] == "Demo Manufacturing Co"
