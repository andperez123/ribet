"""Sector progress and capability unlock tests."""

import io
from pathlib import Path
from uuid import uuid4

from app.models import IngestJob, Organization
from app.seed import DEMO_ORG_ID
from app.services.progress import get_org_progress, recompute_org_progress
from app.services.storage import upload_file
from app.worker.process_job import process_job

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
API_KEY = "dev-secret"
HEADERS = {"X-API-Key": API_KEY, "X-Org-Id": str(DEMO_ORG_ID)}


def _ensure_org(db):
    org = db.get(Organization, DEMO_ORG_ID)
    if not org:
        db.add(Organization(id=DEMO_ORG_ID, name="Test", erp_family="jobboss"))
        db.commit()


def _done_job(db, sector: str, file_name: str = "test.csv"):
    job = IngestJob(
        org_id=DEMO_ORG_ID,
        file_name=file_name,
        storage_key=f"test/{uuid4()}/{file_name}",
        status="done",
        sector=sector,
        report_type="unknown",
    )
    db.add(job)
    db.commit()
    return job


def test_upload_persists_sector(client):
    from app.database import SessionLocal

    _ensure_org(SessionLocal())
    content = (FIXTURES / "ar_aging_jobboss.csv").read_bytes()
    files = {"files": ("ar_aging_jobboss.csv", io.BytesIO(content), "text/csv")}
    data = {"sector": "financials", "consent_acknowledged": "true"}

    r = client.post("/v1/ingest/uploads", headers=HEADERS, files=files, data=data)
    assert r.status_code == 200
    jobs = r.json()["jobs"]
    assert len(jobs) == 1
    assert jobs[0]["sector"] == "financials"


def test_invalid_sector_rejected(client):
    from app.database import SessionLocal

    _ensure_org(SessionLocal())
    content = b"a,b\n1,2\n"
    files = {"files": ("bad.csv", io.BytesIO(content), "text/csv")}
    data = {"sector": "invalid_sector", "consent_acknowledged": "true"}

    r = client.post("/v1/ingest/uploads", headers=HEADERS, files=files, data=data)
    assert r.status_code == 400


def test_financials_unlocks_cash_flow_logistics():
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        _ensure_org(db)
        _done_job(db, "financials")
        progress = recompute_org_progress(db, DEMO_ORG_ID)
        assert "cash_flow_logistics" in progress.unlocked_capabilities
        assert "full_operational_map" not in progress.unlocked_capabilities
    finally:
        db.close()


def test_active_sectors_unlock_core_capabilities():
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        _ensure_org(db)
        for sector in ("financials", "manufacturing"):
            _done_job(db, sector, f"{sector}.csv")
        recompute_org_progress(db, DEMO_ORG_ID)
        data = get_org_progress(db, DEMO_ORG_ID)
        unlocked = {c["id"] for c in data["capabilities"] if c["unlocked"]}
        assert "cash_flow_logistics" in unlocked
        assert "inventory_logistics" in unlocked
        assert data["coverage_count"] == 2
    finally:
        db.close()


def test_orders_sector_fails_as_coming_soon():
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        _ensure_org(db)
        content = b"col_a,col_b\nfoo,bar\n"
        job = IngestJob(
            org_id=DEMO_ORG_ID,
            file_name="orders_export.csv",
            storage_key="",
            status="pending",
            sector="orders",
            errors=[],
        )
        db.add(job)
        db.flush()
        job.storage_key = upload_file(DEMO_ORG_ID, job.id, job.file_name, content)
        db.commit()

        process_job(db, job)
        db.refresh(job)
        assert job.status == "error"
        assert job.errors
        err = job.errors[0]
        assert isinstance(err, dict)
        assert err.get("code") == "sector_disabled"
        assert "not available" in err.get("message", "").lower()
    finally:
        db.close()
