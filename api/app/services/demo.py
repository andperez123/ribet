from __future__ import annotations

"""Demo org seeding from fixture CSVs."""

import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    Customer,
    DataGapRequest,
    GlTransaction,
    HealthSnapshot,
    IngestJob,
    InventoryItem,
    Invoice,
    OperationalFinding,
    OperationalMemory,
    OperationalReport,
    OperationalSnapshot,
    OrgBenchmarkEligibility,
    Organization,
    OrgProgress,
    ProductEvent,
    Vendor,
)
from app.seed import DEMO_ORG_B_ID, DEMO_ORG_ID
from app.services.events import emit_event
from app.services.ingest import validate_file
from app.services.sectors import validate_sector
from app.services.storage import upload_file

def _fixtures_dir() -> Path:
    """api/fixtures in Docker; repo-root/fixtures in local monorepo dev."""
    api_local = Path(__file__).resolve().parents[2] / "fixtures"
    if api_local.is_dir():
        return api_local
    return Path(__file__).resolve().parents[3] / "fixtures"

FIXTURE_SECTORS: dict[str, str] = {
    "ar_aging_jobboss.csv": "financials",
    "ap_aging_jobboss.csv": "financials",
    "gl_detail_jobboss.csv": "financials",
    "inventory_jobboss.csv": "manufacturing",
}


def _create_job_from_bytes(
    db: Session,
    org: Organization,
    filename: str,
    content: bytes,
    sector: str | None,
) -> IngestJob:
    validate_file(filename, content, settings.max_upload_bytes)
    validated_sector = validate_sector(sector)

    job = IngestJob(
        org_id=org.id,
        file_name=filename,
        mime_type="text/csv",
        storage_key="",
        status="pending",
        errors=[],
        sector=validated_sector,
    )
    db.add(job)
    db.flush()
    job.storage_key = upload_file(org.id, job.id, filename, content)
    emit_event(
        db,
        "file_uploaded",
        org_id=org.id,
        job_id=job.id,
        metadata={"file_name": filename, "sector": validated_sector, "demo": True},
    )
    return job


def create_demo_organization(db: Session) -> tuple[Organization, list[IngestJob]]:
    short_id = uuid.uuid4().hex[:8]
    org = Organization(
        name=f"Demo {short_id}",
        erp_family="jobboss",
    )
    db.add(org)
    db.flush()

    jobs: list[IngestJob] = []
    fixtures_dir = _fixtures_dir()
    if not fixtures_dir.is_dir():
        db.commit()
        db.refresh(org)
        return org, jobs

    for path in sorted(fixtures_dir.glob("*.csv")):
        sector = FIXTURE_SECTORS.get(path.name)
        if not sector:
            continue
        content = path.read_bytes()
        job = _create_job_from_bytes(db, org, path.name, content, sector)
        jobs.append(job)

    db.commit()
    for j in jobs:
        db.refresh(j)
    db.refresh(org)
    return org, jobs


def _delete_org_cascade(db: Session, org_id: uuid.UUID) -> None:
    """Remove an org and all dependent rows (FK-safe order)."""
    from sqlalchemy import delete

    oid = org_id
    db.execute(delete(OperationalFinding).where(OperationalFinding.org_id == oid))
    db.execute(delete(HealthSnapshot).where(HealthSnapshot.org_id == oid))
    db.execute(delete(ProductEvent).where(ProductEvent.org_id == oid))
    db.execute(delete(DataGapRequest).where(DataGapRequest.org_id == oid))
    db.execute(delete(OperationalMemory).where(OperationalMemory.org_id == oid))
    db.execute(delete(OperationalSnapshot).where(OperationalSnapshot.org_id == oid))
    db.execute(delete(OrgProgress).where(OrgProgress.org_id == oid))
    db.execute(delete(OrgBenchmarkEligibility).where(OrgBenchmarkEligibility.org_id == oid))
    db.execute(delete(Customer).where(Customer.org_id == oid))
    db.execute(delete(Vendor).where(Vendor.org_id == oid))
    db.execute(delete(GlTransaction).where(GlTransaction.org_id == oid))
    db.execute(delete(Invoice).where(Invoice.org_id == oid))
    db.execute(delete(InventoryItem).where(InventoryItem.org_id == oid))
    db.execute(delete(OperationalReport).where(OperationalReport.org_id == oid))
    db.execute(delete(IngestJob).where(IngestJob.org_id == oid))
    db.execute(delete(Organization).where(Organization.id == oid))


def purge_old_demo_orgs(db: Session, max_age_hours: int = 24) -> int:
    """Delete ephemeral demo orgs older than max_age_hours. Returns count deleted."""
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    protected = {DEMO_ORG_ID, DEMO_ORG_B_ID}
    old_orgs = (
        db.query(Organization)
        .filter(
            Organization.name.like("Demo %"),
            Organization.created_at < cutoff,
            Organization.id.notin_(protected),
        )
        .all()
    )
    count = 0
    for org in old_orgs:
        _delete_org_cascade(db, org.id)
        count += 1
    if count:
        db.commit()
    return count
