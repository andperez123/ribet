"""Persist and apply org-level column mapping corrections — safe schema memory."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from app.models import Organization
from app.services.etl.field_mapper import FieldMapping, MappingPlan


def _headers_hash(columns: list[str]) -> str:
    normalized = "|".join(sorted(c.lower().strip() for c in columns))
    return hashlib.sha256(normalized.encode()).hexdigest()[:32]


def _fingerprint(columns: list[str], report_type: str) -> str:
    normalized = "|".join(sorted(c.lower().strip() for c in columns))
    raw = f"{report_type}:{normalized}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@dataclass
class SchemaMemoryMatch:
    match: str  # auto_apply | suggest | none
    prior_mapping: dict[str, Any] | None = None
    headers_hash: str | None = None

    def to_dict(self) -> dict:
        return {
            "match": self.match,
            "prior_mapping": self.prior_mapping,
            "headers_hash": self.headers_hash,
        }


def check_schema_memory(
    org: Organization,
    report_type: str,
    columns: list[str],
) -> SchemaMemoryMatch:
    memory: dict[str, Any] = org.mapping_memory or {}
    fp = _fingerprint(columns, report_type)
    hhash = _headers_hash(columns)
    entry = memory.get(fp) or memory.get(report_type)
    if not entry:
        return SchemaMemoryMatch(match="none")

    same_headers = entry.get("headers_hash") == hhash or entry.get("schema_fingerprint") == fp
    same_classification = entry.get("report_type") == report_type
    user_confirmed = entry.get("user_confirmed", False)

    if same_headers and same_classification and user_confirmed:
        return SchemaMemoryMatch(match="auto_apply", prior_mapping=entry, headers_hash=hhash)

    if entry.get("column_map") or entry.get("mapping_answers"):
        return SchemaMemoryMatch(match="suggest", prior_mapping=entry, headers_hash=hhash)

    return SchemaMemoryMatch(match="none")


def apply_org_mapping_memory(
    org: Organization,
    plan: MappingPlan,
    columns: list[str],
    *,
    force: bool = False,
) -> MappingPlan:
    """Apply saved mapping only when safe auto-apply conditions are met."""
    match = check_schema_memory(org, plan.report_type, columns)
    if match.match != "auto_apply" and not force:
        return plan

    entry = match.prior_mapping
    if not entry:
        return plan

    saved_map: dict[str, str] = entry.get("column_map") or {}
    if saved_map:
        for orig, canonical in saved_map.items():
            if orig not in columns or not canonical:
                continue
            plan.column_map[orig] = canonical
            plan.field_mapping[canonical] = FieldMapping(source=orig, confidence=1.0)

    if entry.get("amount_strategy"):
        plan.amount_strategy = entry["amount_strategy"]

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
    *,
    mapping_answers: dict[str, str] | None = None,
    row_meaning: str | None = None,
) -> None:
    """Remember user-confirmed mappings for future uploads."""
    if not plan.column_map and not mapping_answers:
        return
    memory = dict(org.mapping_memory or {})
    fp = _fingerprint(columns, plan.report_type)
    hhash = _headers_hash(columns)
    memory[fp] = {
        "report_type": plan.report_type,
        "column_map": dict(plan.column_map),
        "schema_fingerprint": fp,
        "headers_hash": hhash,
        "amount_strategy": plan.amount_strategy,
        "mapping_answers": dict(mapping_answers or {}),
        "row_meaning": row_meaning,
        "user_confirmed": True,
    }
    memory[plan.report_type] = memory[fp]
    org.mapping_memory = memory
