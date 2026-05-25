from __future__ import annotations

"""Org sector coverage and capability unlock tracking."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import IngestJob, OrgProgress
from app.services.sectors import (
    CAPABILITIES,
    SECTORS,
    SECTOR_LABELS,
    capability_requirement_text,
    evaluate_capabilities,
)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()


def recompute_org_progress(db: Session, org_id: UUID) -> OrgProgress:
    jobs = (
        db.query(IngestJob)
        .filter(
            IngestJob.org_id == org_id,
            IngestJob.status == "done",
            IngestJob.sector.isnot(None),
        )
        .order_by(IngestJob.updated_at.desc())
        .all()
    )

    sectors_covered: dict[str, dict] = {}
    for job in jobs:
        sector = job.sector
        if not sector:
            continue
        entry = sectors_covered.get(sector)
        uploaded_at = job.updated_at or job.created_at
        if entry is None:
            sectors_covered[sector] = {
                "count": 1,
                "last_upload_at": _iso(uploaded_at),
                "last_report_type": job.report_type,
            }
        else:
            entry["count"] += 1
            if uploaded_at and (
                entry.get("last_upload_at") is None
                or uploaded_at.isoformat() > entry["last_upload_at"]
            ):
                entry["last_upload_at"] = _iso(uploaded_at)
                entry["last_report_type"] = job.report_type

    covered_set = set(sectors_covered.keys())
    unlocked = evaluate_capabilities(covered_set)

    progress = db.get(OrgProgress, org_id)
    if progress is None:
        progress = OrgProgress(org_id=org_id)
        db.add(progress)

    progress.sectors_covered = sectors_covered
    progress.unlocked_capabilities = unlocked
    progress.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(progress)
    return progress


def get_org_progress(db: Session, org_id: UUID) -> dict:
    progress = db.get(OrgProgress, org_id)
    if progress is None:
        progress = recompute_org_progress(db, org_id)

    covered = progress.sectors_covered or {}
    unlocked_set = set(progress.unlocked_capabilities or [])

    sectors_out = []
    for sector_id in SECTORS:
        info = covered.get(sector_id)
        sectors_out.append(
            {
                "id": sector_id,
                "label": SECTOR_LABELS[sector_id],
                "covered": info is not None and info.get("count", 0) > 0,
                "count": info.get("count", 0) if info else 0,
                "last_upload_at": info.get("last_upload_at") if info else None,
                "last_report_type": info.get("last_report_type") if info else None,
            }
        )

    capabilities_out = []
    for cap in CAPABILITIES:
        cap_id = str(cap["id"])
        is_unlocked = cap_id in unlocked_set
        capabilities_out.append(
            {
                "id": cap_id,
                "name": str(cap["name"]),
                "description": str(cap["description"]),
                "unlocked": is_unlocked,
                "requirement": None if is_unlocked else capability_requirement_text(cap),
            }
        )

    coverage_count = sum(1 for s in sectors_out if s["covered"])

    return {
        "sectors": sectors_out,
        "capabilities": capabilities_out,
        "coverage_count": coverage_count,
    }
