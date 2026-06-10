"""Orchestrate upload interpretation: profile → classify → map → questions → readiness."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from app.models import Organization
from app.services.etl.aliases import detect_aging_bucket_columns, get_detailed_column_mappings
from app.services.etl.classifier import DatasetClassification, classify_dataset
from app.services.etl.field_mapper import FieldMapping, MappingPlan, propose_mapping
from app.services.etl.profiler import DataProfile, profile_upload
from app.services.etl.readiness import AnalysisReadiness, compute_analysis_readiness
from app.services.etl.types import ColumnMappingDetail
from app.services.etl.question_registry import IngestionQuestion, generate_questions
from app.services.etl.row_meaning import RowMeaning, infer_row_meaning
from app.services.mapping_memory import SchemaMemoryMatch, check_schema_memory


@dataclass
class InterpretationResult:
    data_profile: DataProfile
    classification: DatasetClassification
    row_meaning: RowMeaning
    mapping_plan: MappingPlan
    column_mappings: list[ColumnMappingDetail] = field(default_factory=list)
    questions: list[IngestionQuestion] = field(default_factory=list)
    readiness: AnalysisReadiness | None = None
    schema_memory: SchemaMemoryMatch | None = None
    missing_fields: list[str] = field(default_factory=list)
    mapping_answers: dict[str, str] = field(default_factory=dict)

    def to_metadata(self) -> dict:
        meta = {
            **self.mapping_plan.to_dict(),
            "data_profile": self.data_profile.to_dict(),
            "classification": self.classification.to_dict(),
            "row_meaning": self.row_meaning.to_dict(),
            "column_mappings": [cm.to_dict() for cm in self.column_mappings],
            "questions": [q.to_dict() for q in self.questions],
            "missing_fields": self.missing_fields,
            "mapping_answers": self.mapping_answers,
        }
        if self.readiness:
            meta["analysis_readiness"] = self.readiness.to_dict()
        if self.schema_memory:
            meta["schema_memory"] = self.schema_memory.to_dict()
        return meta


def _build_column_mappings(
    columns: list[str],
    col_map: dict[str, str],
    field_mapping: dict[str, FieldMapping],
) -> list[ColumnMappingDetail]:
    details_map: dict[str, ColumnMappingDetail] = {}
    for col, canonical, score, reason in get_detailed_column_mappings(columns):
        details_map[col] = ColumnMappingDetail(
            source_column=col,
            canonical_field=canonical if col in col_map else None,
            confidence=score,
            reason=reason,
            needs_user_confirmation=score < 0.75,
        )

    for col in columns:
        if col not in details_map:
            canonical = col_map.get(col)
            fm = field_mapping.get(canonical) if canonical else None
            conf = fm.confidence if fm else 0.0
            details_map[col] = ColumnMappingDetail(
                source_column=col,
                canonical_field=canonical,
                confidence=conf,
                reason=f"mapped to {canonical}" if canonical else "unmapped",
                needs_user_confirmation=conf < 0.75 if canonical else False,
            )
        elif col in col_map:
            canonical = col_map[col]
            fm = field_mapping.get(canonical)
            conf = fm.confidence if fm else details_map[col].confidence
            details_map[col].canonical_field = canonical
            details_map[col].confidence = conf
            details_map[col].needs_user_confirmation = conf < 0.75

    unmapped = [c for c in columns if c not in col_map]
    for col in unmapped:
        if col in details_map:
            details_map[col].canonical_field = None
            details_map[col].reason = "unmapped column"

    return [details_map[c] for c in columns if c in details_map]


def _missing_fields(report_type: str, mapping_plan: MappingPlan) -> list[str]:
    from app.services.etl.field_mapper import _REQUIRED_FIELDS

    required = list(_REQUIRED_FIELDS.get(report_type, []))
    if report_type == "gl_trial_balance":
        required = ["account_id"]
    missing: list[str] = []
    for req in required:
        fm = mapping_plan.field_mapping.get(req)
        if not fm or (not fm.source and fm.strategy == "single_column"):
            missing.append(req)
    if report_type == "gl_trial_balance":
        if mapping_plan.amount_strategy == "needs_user_choice":
            missing.append("amount_strategy")
    return missing


def interpret_upload(
    df: pd.DataFrame,
    filename: str,
    org: Organization | None = None,
    sector_hint: str | None = None,
    mapping_answers: dict[str, str] | None = None,
    user_confirmed: bool = False,
) -> InterpretationResult:
    data_profile = profile_upload(df, filename)
    classification = classify_dataset(
        filename,
        data_profile.headers,
        data_profile.column_profiles,
        data_profile=data_profile,
        sector_hint=sector_hint,
    )
    report_type = classification.likely_type
    if report_type == "unknown_operational_export":
        report_type = "unknown"

    row_meaning = infer_row_meaning(classification)
    answers = dict(mapping_answers or {})
    if answers.get("row_meaning"):
        row_meaning.user_confirmed = answers["row_meaning"]

    mapping_plan = propose_mapping(
        data_profile.column_profiles,
        report_type if report_type != "unknown_operational_export" else "unknown",
        data_profile.headers,
    )
    mapping_plan.report_type = classification.likely_type

    if answers.get("gl_amount_semantics"):
        mapping_plan.amount_strategy = answers["gl_amount_semantics"]

    schema_memory = None
    if org:
        schema_memory = check_schema_memory(org, classification.likely_type, data_profile.headers)
        if schema_memory.match == "auto_apply" and schema_memory.prior_mapping:
            prior = schema_memory.prior_mapping
            if prior.get("column_map"):
                mapping_plan.column_map.update(prior["column_map"])
                for orig, canonical in prior["column_map"].items():
                    mapping_plan.field_mapping[canonical] = FieldMapping(
                        source=orig, confidence=1.0
                    )
            if prior.get("amount_strategy"):
                mapping_plan.amount_strategy = prior["amount_strategy"]
            if prior.get("mapping_answers"):
                answers.update(prior["mapping_answers"])
            if prior.get("row_meaning"):
                row_meaning.user_confirmed = prior["row_meaning"]

    column_mappings = _build_column_mappings(
        data_profile.headers,
        mapping_plan.column_map,
        mapping_plan.field_mapping,
    )
    questions = generate_questions(
        classification,
        mapping_plan,
        column_mappings,
        row_meaning,
        data_profile,
        answers,
    )
    missing = _missing_fields(classification.likely_type, mapping_plan)
    readiness = compute_analysis_readiness(
        report_type=classification.likely_type,
        row_count=data_profile.row_count,
        mapping_plan=mapping_plan,
        column_mappings=column_mappings,
        questions=questions,
        row_meaning=row_meaning,
        mapping_answers=answers,
        user_confirmed_mappings=user_confirmed,
    )

    return InterpretationResult(
        data_profile=data_profile,
        classification=classification,
        row_meaning=row_meaning,
        mapping_plan=mapping_plan,
        column_mappings=column_mappings,
        questions=questions,
        readiness=readiness,
        schema_memory=schema_memory,
        missing_fields=missing,
        mapping_answers=answers,
    )
