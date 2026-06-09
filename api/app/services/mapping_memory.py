"""Persist and apply org-level column mapping corrections."""

from __future__ import annotations

import hashlib
from typing import Any

from app.models import Organization
from app.services.etl.field_mapper import FieldMapping, MappingPlan


def _fingerprint(columns: list[str], report_type: str) -> str:
    normalized = "|".join(sorted(c.lower().strip() for c in columns))
    raw = f"{report_type}:{normalized}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def apply_org_mapping_memory(
    org: Organization,
    plan: MappingPlan,
    columns: list[str],
) -> MappingPlan:
    """Boost confidence when org has confirmed mappings for this schema."""
    memory: dict[str, Any] = org.mapping_memory or {}
    fp = _fingerprint(columns, plan.report_type)
    entry = memory.get(fp) or memory.get(plan.report_type)
    if not entry:
        return plan

    saved_map: dict[str, str] = entry.get("column_map") or {}
    if not saved_map:
        return plan

    for orig, canonical in saved_map.items():
        if orig not in columns or not canonical:
            continue
        plan.column_map[orig] = canonical
        plan.field_mapping[canonical] = FieldMapping(source=orig, confidence=1.0)

    mapped_sources = {fm.source for fm in plan.field_mapping.values() if fm.source}
    mapped_sources.update(s for fm in plan.field_mapping.values() for s in fm.sources)
    plan.unmapped_columns = [
        c for c in columns if c not in mapped_sources and c not in plan.bucket_columns
    ]
    plan.overall_confidence = max(plan.overall_confidence, 0.9)
    return plan


def save_org_mapping_memory(
    org: Organization,
    plan: MappingPlan,
    columns: list[str],
) -> None:
    """Remember user-confirmed column_map for future uploads."""
    if not plan.column_map:
        return
    memory = dict(org.mapping_memory or {})
    fp = _fingerprint(columns, plan.report_type)
    memory[fp] = {
        "report_type": plan.report_type,
        "column_map": dict(plan.column_map),
        "schema_fingerprint": fp,
    }
    memory[plan.report_type] = memory[fp]
    org.mapping_memory = memory
