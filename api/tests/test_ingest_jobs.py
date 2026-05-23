"""List ingest jobs endpoint."""

from datetime import datetime, timedelta, timezone

from app.models import IngestJob, Organization
from app.seed import DEMO_ORG_B_ID, DEMO_ORG_ID

API_KEY = "dev-secret"
HEADERS_A = {"X-API-Key": API_KEY, "X-Org-Id": str(DEMO_ORG_ID)}
HEADERS_B = {"X-API-Key": API_KEY, "X-Org-Id": str(DEMO_ORG_B_ID)}


def _seed_orgs(client):
    from app.database import SessionLocal

    db = SessionLocal()
    for oid, name in [(DEMO_ORG_ID, "A"), (DEMO_ORG_B_ID, "B")]:
        if not db.get(Organization, oid):
            db.add(Organization(id=oid, name=name, erp_family="jobboss"))
    db.commit()
    db.close()


def _add_job(db, org_id, file_name: str, minutes_ago: int = 0):
    now = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    job = IngestJob(
        org_id=org_id,
        file_name=file_name,
        storage_key=f"test/{file_name}",
        status="done",
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_list_jobs_ordered_and_limited(client):
    _seed_orgs(client)
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        _add_job(db, DEMO_ORG_ID, "oldest.csv", minutes_ago=30)
        _add_job(db, DEMO_ORG_ID, "middle.csv", minutes_ago=15)
        newest = _add_job(db, DEMO_ORG_ID, "newest.csv", minutes_ago=0)
    finally:
        db.close()

    r = client.get("/v1/ingest/jobs", headers=HEADERS_A, params={"limit": 2})
    assert r.status_code == 200
    jobs = r.json()["jobs"]
    assert len(jobs) == 2
    assert jobs[0]["file_name"] == "newest.csv"
    assert jobs[0]["id"] == str(newest.id)
    assert jobs[0]["created_at"] is not None
    assert jobs[1]["file_name"] == "middle.csv"


def test_list_jobs_org_isolation(client):
    _seed_orgs(client)
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        _add_job(db, DEMO_ORG_ID, "org_a_only.csv")
        _add_job(db, DEMO_ORG_B_ID, "org_b_only.csv")
    finally:
        db.close()

    r_a = client.get("/v1/ingest/jobs", headers=HEADERS_A)
    assert r_a.status_code == 200
    names_a = {j["file_name"] for j in r_a.json()["jobs"]}
    assert "org_a_only.csv" in names_a
    assert "org_b_only.csv" not in names_a

    r_b = client.get("/v1/ingest/jobs", headers=HEADERS_B)
    names_b = {j["file_name"] for j in r_b.json()["jobs"]}
    assert "org_b_only.csv" in names_b
    assert "org_a_only.csv" not in names_b
