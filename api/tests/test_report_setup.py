"""Report Sources & Assumptions — setup draft, validation, regenerate."""

import uuid

import pytest

from app.models import IngestJob, OperationalReport, OperationalReportSourceJob, Organization
from app.seed import DEMO_ORG_ID

API_KEY = "dev-secret"


def _headers(org_id: uuid.UUID) -> dict[str, str]:
    return {"X-API-Key": API_KEY, "X-Org-Id": str(org_id)}


def _done_job(db, org_id: uuid.UUID, **kwargs) -> IngestJob:
    job = IngestJob(
        org_id=org_id,
        file_name=kwargs.get("file_name", "ar.csv"),
        storage_key="test/key",
        status="done",
        report_type=kwargs.get("report_type", "ar_aging"),
        detected_period=kwargs.get("detected_period", "2026-06"),
        row_count=kwargs.get("row_count", 100),
        mapping_confidence=kwargs.get("mapping_confidence", 0.95),
        errors=[],
    )
    db.add(job)
    db.flush()
    return job


def test_setup_get_defaults_to_all_done_jobs(client):
    org_id = uuid.uuid4()
    from app.database import SessionLocal

    db = SessionLocal()
    org = Organization(id=org_id, name="Setup Test", erp_family="jobboss")
    db.add(org)
    j1 = _done_job(db, org_id, file_name="a.csv")
    j2 = _done_job(db, org_id, file_name="b.csv", report_type="ap_aging")
    j1_id, j2_id = j1.id, j2.id
    db.commit()
    db.close()

    res = client.get("/v1/reports/setup", headers=_headers(org_id))
    assert res.status_code == 200
    data = res.json()
    assert len(data["available_jobs"]) == 2
    assert set(data["draft"]["source_job_ids"]) == {str(j1_id), str(j2_id)}


def test_setup_rejects_empty_selection(client):
    org_id = uuid.uuid4()
    from app.database import SessionLocal

    db = SessionLocal()
    db.add(Organization(id=org_id, name="Empty", erp_family="jobboss"))
    db.commit()
    db.close()

    res = client.put(
        "/v1/reports/setup",
        headers=_headers(org_id),
        json={"source_job_ids": []},
    )
    assert res.status_code == 400


def test_setup_warnings_duplicate_domain(client):
    org_id = uuid.uuid4()
    from app.database import SessionLocal

    db = SessionLocal()
    db.add(Organization(id=org_id, name="Dup", erp_family="jobboss"))
    _done_job(db, org_id, file_name="ar1.csv", report_type="ar_aging")
    _done_job(db, org_id, file_name="ar2.csv", report_type="ar_aging")
    db.commit()
    db.close()

    res = client.get("/v1/reports/setup?preview=true", headers=_headers(org_id))
    assert res.status_code == 200
    codes = {w["code"] for w in res.json()["warnings"]}
    assert "duplicate_domain" in codes


def test_regenerate_subset_creates_source_join_rows(client):
    org_id = uuid.uuid4()
    from app.database import SessionLocal
    from app.services.report import generate_report

    db = SessionLocal()
    db.add(Organization(id=org_id, name="Regen", erp_family="jobboss"))
    j1 = _done_job(db, org_id, file_name="ar.csv")
    j2 = _done_job(db, org_id, file_name="ap.csv", report_type="ap_aging")
    j1_id, j2_id = j1.id, j2.id
    db.commit()

    generate_report(db, org_id, [j1_id, j2_id])
    db.close()

    res = client.post(
        "/v1/reports/regenerate",
        headers=_headers(org_id),
        json={"source_job_ids": [str(j1_id)]},
    )
    assert res.status_code == 200
    report_id = uuid.UUID(res.json()["id"])

    db = SessionLocal()
    rows = (
        db.query(OperationalReportSourceJob)
        .filter(OperationalReportSourceJob.report_id == report_id)
        .all()
    )
    assert len(rows) == 1
    assert rows[0].ingest_job_id == j1_id
    assert db.get(IngestJob, j1_id).report_id == report_id
    assert db.get(IngestJob, j2_id).report_id is None
    snap = db.get(OperationalReport, report_id).generation_context
    assert snap["source_context_hash"]
    assert snap["regenerate_mode"] == "full"
    db.close()


def test_context_hash_stable(client):
    from app.services.report_context import ReportGenerationContext, compute_source_context_hash

    ctx = ReportGenerationContext(source_job_ids=[uuid.uuid4(), uuid.uuid4()])
    h1 = compute_source_context_hash(ctx)
    h2 = compute_source_context_hash(ctx)
    assert h1 == h2


def test_report_setup_snapshot_endpoint(client):
    org_id = DEMO_ORG_ID
    res = client.post(
        "/v1/reports/regenerate",
        headers=_headers(org_id),
        json={},
    )
    if res.status_code != 200:
        pytest.skip("Demo org has no uploads")
    report_id = res.json()["id"]
    snap_res = client.get(f"/v1/reports/{report_id}/setup", headers=_headers(org_id))
    assert snap_res.status_code == 200
    assert snap_res.json()["sources"]
