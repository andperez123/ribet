"""Admin metrics API tests."""

from app.models import Organization
from app.seed import DEMO_ORG_ID

ADMIN_KEY = "dev-admin-secret"
ADMIN_HEADERS = {"X-Admin-Key": ADMIN_KEY}


def _seed_org(client):
    from app.database import SessionLocal

    db = SessionLocal()
    if not db.get(Organization, DEMO_ORG_ID):
        db.add(
            Organization(
                id=DEMO_ORG_ID,
                name="Demo Manufacturing Co",
                erp_family="jobboss",
            )
        )
    db.commit()
    db.close()


def test_admin_metrics_requires_key(client):
    r = client.get("/v1/admin/metrics")
    assert r.status_code == 401


def test_admin_metrics_returns_kpis(client):
    _seed_org(client)
    r = client.get("/v1/admin/metrics", headers=ADMIN_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "totals" in data
    assert "activation" in data
    assert "engagement" in data
    assert "weekly" in data
    assert "orgs" in data
    assert data["totals"]["orgs"] >= 1
    assert any(o["org_id"] == str(DEMO_ORG_ID) for o in data["orgs"])
