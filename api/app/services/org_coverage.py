from __future__ import annotations

"""Build org coverage + confidence API payloads."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import DataGapRequest
from app.services.gaps import get_open_gaps
from app.services.graph.confidence import compute_analysis_confidence
from app.services.graph.coverage import get_graph_coverage


def build_org_coverage_payload(db: Session, org_id: UUID) -> dict:
    coverage = get_graph_coverage(db, org_id)
    confidence = compute_analysis_confidence(coverage)
    gaps = get_open_gaps(db, org_id)

    next_upload = confidence.next_upload

    return {
        "understood": [
            {
                "key": i.key,
                "label": i.label,
                "sector": i.sector,
                "covered": True,
                "uploadable": i.uploadable,
            }
            for i in coverage.understood
        ],
        "needed": [
            {
                "key": i.key,
                "label": i.label,
                "sector": i.sector,
                "covered": False,
                "uploadable": i.uploadable,
            }
            for i in coverage.needed
        ],
        "analysis_confidence": confidence.score,
        "confidence_breakdown": [
            {
                "key": b.key,
                "label": b.label,
                "weight": b.weight,
                "covered": b.covered,
            }
            for b in confidence.breakdown
        ],
        "next_upload": (
            {
                "key": next_upload.key,
                "label": next_upload.label,
                "confidence_if_uploaded": next_upload.confidence_if_uploaded,
            }
            if next_upload
            else None
        ),
        "gaps": [_gap_to_dict(g) for g in gaps],
    }


def _gap_to_dict(g: DataGapRequest) -> dict:
    return {
        "id": str(g.id),
        "gap_type": g.gap_type,
        "reason": g.reason,
        "recommended_uploads": list(g.recommended_uploads or []),
        "requested_report_types": list(g.requested_report_types or []),
        "requested_sector": g.requested_sector,
        "confidence_if_uploaded": g.confidence_if_uploaded,
        "priority": g.priority,
        "status": g.status,
    }
