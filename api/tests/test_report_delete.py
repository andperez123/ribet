"""Report deletion and personal workspace org provisioning."""

import uuid

from app.models import (
    HealthSnapshot,
    IngestJob,
    OperationalFinding,
    OperationalReport,
    Organization,
)
from app.seed import DEMO_ORG_ID

API_KEY = "dev-secret"


def _headers(org_id: uuid.UUID) -> dict[str, str]:
    return {"X-API-Key": API_KEY, "X-Org-Id": str(org_id)}


def test_personal_workspace_org_is_isolated(client):
    user_a = "user_test_personal_a"
    user_b = "user_test_personal_b"

    for clerk_id, name in [(user_a, "User A"), (user_b, "User B")]:
        res = client.post(
            "/v1/org/from-clerk",
            headers={"X-API-Key": API_KEY},
            json={"clerk_org_id": clerk_id, "name": name},
        )
        assert res.status_code == 200
        assert res.json()["created"] is True

    res_a = client.post(
        "/v1/org/from-clerk",
        headers={"X-API-Key": API_KEY},
        json={"clerk_org_id": user_a, "name": "User A"},
    )
    assert res_a.json()["created"] is False
    org_a = uuid.UUID(res_a.json()["org_id"])

    res_b = client.post(
        "/v1/org/from-clerk",
        headers={"X-API-Key": API_KEY},
        json={"clerk_org_id": user_b, "name": "User B"},
    )
    org_b = uuid.UUID(res_b.json()["org_id"])
    assert org_a != org_b


def test_delete_report_removes_report_and_findings(client):
    from app.database import SessionLocal

    org_id = DEMO_ORG_ID
    db = SessionLocal()
    if not db.get(Organization, org_id):
        db.add(Organization(id=org_id, name="Demo", erp_family="jobboss"))
        db.commit()

    report = OperationalReport(org_id=org_id, job_ids=[], health_score=70)
    db.add(report)
    db.flush()

    job = IngestJob(
        org_id=org_id,
        file_name="test.csv",
        storage_key="test/key",
        status="done",
        report_id=report.id,
    )
    db.add(job)
    db.add(
        OperationalFinding(
            org_id=org_id,
            report_id=report.id,
            finding_type="test",
            title="Test finding",
            detail="detail",
            severity="low",
            business_impact="low",
            department="finance",
            category="test",
            fingerprint="fp-test-delete",
        )
    )
    db.add(
        HealthSnapshot(
            org_id=org_id,
            report_id=report.id,
            score=70,
            status="Stable",
        )
    )
    db.commit()
    report_id = report.id
    db.close()

    res = client.delete(f"/v1/reports/{report_id}", headers=_headers(org_id))
    assert res.status_code == 200
    assert res.json()["deleted"] is True

    db = SessionLocal()
    assert db.get(OperationalReport, report_id) is None
    findings = (
        db.query(OperationalFinding)
        .filter(OperationalFinding.report_id == report_id)
        .count()
    )
    assert findings == 0
    refreshed_job = db.get(IngestJob, job.id)
    assert refreshed_job is not None
    assert refreshed_job.report_id is None
    db.close()


def test_delete_report_wrong_org_returns_404(client):
    from app.database import SessionLocal

    org_a = uuid.uuid4()
    org_b = uuid.uuid4()
    db = SessionLocal()
    db.add(Organization(id=org_a, name="A", erp_family="jobboss"))
    db.add(Organization(id=org_b, name="B", erp_family="jobboss"))
    report = OperationalReport(org_id=org_a, job_ids=[], health_score=50)
    db.add(report)
    db.commit()
    report_id = report.id
    db.close()

    res = client.delete(f"/v1/reports/{report_id}", headers=_headers(org_b))
    assert res.status_code == 404
