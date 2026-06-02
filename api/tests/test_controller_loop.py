"""AI Controller loop — AR upload → AP gap → AP upload → confidence rises."""

from pathlib import Path

from app.models import DataGapRequest, Organization
from app.seed import DEMO_ORG_ID
from app.services.graph.confidence import compute_analysis_confidence
from app.services.graph.coverage import get_graph_coverage
from app.worker.process_job import process_job

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def _run_fixture(db, org_id, filename: str, sector: str):
    from app.models import IngestJob
    from app.services.storage import upload_file

    content = (FIXTURES / filename).read_bytes()
    job = IngestJob(
        org_id=org_id,
        file_name=filename,
        storage_key="",
        status="pending",
        errors=[],
        sector=sector,
        consent_acknowledged=True,
    )
    db.add(job)
    db.flush()
    job.storage_key = upload_file(org_id, job.id, job.file_name, content)
    db.commit()
    process_job(db, job)
    db.refresh(job)
    return job


def test_ar_upload_detects_missing_ap_gap(client):
    from app.database import SessionLocal

    db = SessionLocal()
    org = Organization(id=DEMO_ORG_ID, name="Controller Test", erp_family="jobboss")
    db.merge(org)
    db.commit()

    job = _run_fixture(db, DEMO_ORG_ID, "ar_aging_jobboss.csv", "financials")
    assert job.status == "done"

    coverage = get_graph_coverage(db, DEMO_ORG_ID)
    assert coverage.has("ar_aging")
    assert not coverage.has("ap_aging")

    confidence = compute_analysis_confidence(coverage)
    assert confidence.score == 15

    gaps = (
        db.query(DataGapRequest)
        .filter(
            DataGapRequest.org_id == DEMO_ORG_ID,
            DataGapRequest.status == "open",
        )
        .all()
    )
    gap_types = {g.gap_type for g in gaps}
    assert "missing_ap_aging" in gap_types

    ap_gap = next(g for g in gaps if g.gap_type == "missing_ap_aging")
    assert "AP Aging" in ap_gap.recommended_uploads
    assert ap_gap.confidence_if_uploaded == 30

    db.close()


def test_ap_upload_after_ar_raises_confidence_and_satisfies_gap(client):
    from app.database import SessionLocal

    db = SessionLocal()
    org = Organization(id=DEMO_ORG_ID, name="Controller Test", erp_family="jobboss")
    db.merge(org)
    db.commit()

    _run_fixture(db, DEMO_ORG_ID, "ar_aging_jobboss.csv", "financials")
    _run_fixture(db, DEMO_ORG_ID, "ap_aging_jobboss.csv", "financials")

    coverage = get_graph_coverage(db, DEMO_ORG_ID)
    assert coverage.has("ar_aging")
    assert coverage.has("ap_aging")

    confidence = compute_analysis_confidence(coverage)
    assert confidence.score == 30

    open_gaps = (
        db.query(DataGapRequest)
        .filter(
            DataGapRequest.org_id == DEMO_ORG_ID,
            DataGapRequest.status == "open",
            DataGapRequest.gap_type == "missing_ap_aging",
        )
        .all()
    )
    assert len(open_gaps) == 0

    satisfied = (
        db.query(DataGapRequest)
        .filter(
            DataGapRequest.org_id == DEMO_ORG_ID,
            DataGapRequest.gap_type == "missing_ap_aging",
            DataGapRequest.status == "satisfied",
        )
        .first()
    )
    assert satisfied is not None

    db.close()


def test_cross_sector_finding_with_ar_and_inventory(client):
    from app.database import SessionLocal
    from app.models import OperationalFinding

    db = SessionLocal()
    org = Organization(id=DEMO_ORG_ID, name="Controller Test", erp_family="jobboss")
    db.merge(org)
    db.commit()

    _run_fixture(db, DEMO_ORG_ID, "ar_aging_jobboss.csv", "financials")
    job = _run_fixture(db, DEMO_ORG_ID, "inventory_jobboss.csv", "manufacturing")
    assert job.status == "done"

    findings = (
        db.query(OperationalFinding)
        .filter(
            OperationalFinding.org_id == DEMO_ORG_ID,
            OperationalFinding.finding_type == "operational_cash_pressure",
        )
        .all()
    )
    assert len(findings) >= 1

    gaps = (
        db.query(DataGapRequest)
        .filter(
            DataGapRequest.org_id == DEMO_ORG_ID,
            DataGapRequest.status == "open",
        )
        .all()
    )
    gap_types = {g.gap_type for g in gaps}
    assert "cash_pressure_diagnosis" in gap_types or "missing_ap_aging" in gap_types

    db.close()


def test_org_coverage_api(client):
    import uuid

    from app.database import SessionLocal

    org_id = uuid.uuid4()
    db = SessionLocal()
    org = Organization(id=org_id, name="Coverage API Test", erp_family="jobboss")
    db.add(org)
    db.commit()
    _run_fixture(db, org_id, "ar_aging_jobboss.csv", "financials")
    db.close()

    res = client.get(
        "/v1/org/coverage",
        headers={"X-API-Key": "dev-secret", "X-Org-Id": str(org_id)},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["analysis_confidence"] == 15
    assert len(data["understood"]) >= 1
    assert len(data["gaps"]) >= 1
    assert data["next_upload"]["label"] == "AP Aging"
