from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import OperationalMemory
from app.services.rules.runner import RuleFinding

SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def upsert_memory(db: Session, org_id: UUID, findings: list[RuleFinding]) -> None:
    now = datetime.now(timezone.utc)
    for f in findings:
        existing = (
            db.query(OperationalMemory)
            .filter(
                OperationalMemory.org_id == org_id,
                OperationalMemory.fingerprint == f.fingerprint,
            )
            .first()
        )
        if existing:
            existing.last_seen_at = now
            existing.occurrence_count += 1
            if SEVERITY_RANK.get(f.severity, 0) > SEVERITY_RANK.get(existing.severity_peak, 0):
                existing.severity_peak = f.severity
        else:
            db.add(
                OperationalMemory(
                    org_id=org_id,
                    fingerprint=f.fingerprint,
                    finding_type=f.finding_type,
                    title=f.title,
                    first_seen_at=now,
                    last_seen_at=now,
                    occurrence_count=1,
                    severity_peak=f.severity,
                )
            )
