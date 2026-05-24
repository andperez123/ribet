"""Org isolation and API tests."""

from app.models import Organization
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


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_health_ready(client):
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json()["database"] == "connected"


def test_health_score_requires_org(client):
    r = client.get("/v1/health/score", headers={"X-API-Key": API_KEY})
    assert r.status_code == 400


def test_org_b_cannot_see_org_a_report(client):
    _seed_orgs(client)
    r_a = client.get("/v1/reports/latest", headers=HEADERS_A)
    if r_a.status_code == 404:
        return

    report_a_id = r_a.json()["id"]
    r_b = client.get(f"/v1/reports/{report_a_id}", headers=HEADERS_B)
    assert r_b.status_code == 404


def test_invalid_api_key(client):
    r = client.get(
        "/v1/health/score",
        headers={"X-API-Key": "wrong", "X-Org-Id": str(DEMO_ORG_ID)},
    )
    assert r.status_code == 401
