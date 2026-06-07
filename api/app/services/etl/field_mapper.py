"""Heuristic field mapping — produces MappingPlan with confidence scores."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.etl.aliases import (
    detect_aging_bucket_columns,
    normalize_columns,
)
from app.services.etl.profiler import ColumnProfile


@dataclass
class FieldMapping:
    source: str | None
    confidence: float
    strategy: str = "single_column"
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d: dict = {"confidence": round(self.confidence, 3), "strategy": self.strategy}
        if self.source:
            d["source"] = self.source
        if self.sources:
            d["sources"] = self.sources
        return d


@dataclass
class MappingPlan:
    report_type: str
    field_mapping: dict[str, FieldMapping]
    amount_strategy: str = "single_column"
    bucket_columns: list[str] = field(default_factory=list)
    unmapped_columns: list[str] = field(default_factory=list)
    overall_confidence: float = 0.0
    parse_warnings: list[str] = field(default_factory=list)
    column_map: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "report_type": self.report_type,
            "field_mapping": {k: v.to_dict() for k, v in self.field_mapping.items()},
            "amount_strategy": self.amount_strategy,
            "bucket_columns": self.bucket_columns,
            "unmapped_columns": self.unmapped_columns,
            "overall_confidence": round(self.overall_confidence, 3),
            "parse_warnings": self.parse_warnings,
            "column_map": self.column_map,
        }


_REQUIRED_FIELDS: dict[str, list[str]] = {
    "ar_aging": ["customer_name"],
    "ap_aging": ["vendor_name"],
    "gl_detail": ["account_id", "amount"],
    "inventory": ["sku"],
}


def propose_mapping(
    profiles: list[ColumnProfile],
    report_type: str,
    columns: list[str],
) -> MappingPlan:
    col_map = normalize_columns(columns)
    bucket_cols = detect_aging_bucket_columns(columns)
    bucket_names = [c for c, _ in bucket_cols]

    profile_by_name = {p.name: p for p in profiles}
    field_mapping: dict[str, FieldMapping] = {}

    for orig, canonical in col_map.items():
        score = 0.85
        prof = profile_by_name.get(orig)
        if prof and canonical == "amount" and not prof.looks_numeric and not prof.looks_currency:
            score = 0.4
        if prof and canonical in ("customer_name", "vendor_name") and prof.looks_currency:
            score = 0.1
        field_mapping[canonical] = FieldMapping(source=orig, confidence=score)

    amount_strategy = "single_column"
    if report_type in ("ar_aging", "ap_aging"):
        has_amount = "amount" in field_mapping and field_mapping["amount"].confidence >= 0.5
        if bucket_names and (not has_amount or field_mapping.get("amount", FieldMapping(None, 0)).confidence < 0.6):
            amount_strategy = "sum_buckets"
            field_mapping["amount"] = FieldMapping(
                source=None,
                confidence=0.88 if len(bucket_names) >= 2 else 0.6,
                strategy="sum_buckets",
                sources=bucket_names,
            )

    mapped_sources = {fm.source for fm in field_mapping.values() if fm.source}
    mapped_sources.update(
        s for fm in field_mapping.values() for s in fm.sources
    )
    unmapped = [c for c in columns if c not in mapped_sources and c not in bucket_names]

    required = _REQUIRED_FIELDS.get(report_type, [])
    confidences: list[float] = []
    warnings: list[str] = []

    for req in required:
        fm = field_mapping.get(req)
        if not fm or (not fm.source and fm.strategy == "single_column"):
            confidences.append(0.3)
            warnings.append(f"missing required field: {req}")
        else:
            confidences.append(fm.confidence)

    if report_type in ("ar_aging", "ap_aging"):
        amt = field_mapping.get("amount")
        if amt:
            confidences.append(amt.confidence)
        else:
            confidences.append(0.2)
            warnings.append("no amount column or bucket columns detected")

    overall = sum(confidences) / len(confidences) if confidences else 0.5
    if report_type == "unknown":
        overall = min(overall, 0.3)

    return MappingPlan(
        report_type=report_type,
        field_mapping=field_mapping,
        amount_strategy=amount_strategy,
        bucket_columns=bucket_names,
        unmapped_columns=unmapped,
        overall_confidence=overall,
        parse_warnings=warnings,
        column_map=col_map,
    )
