"""Analysis readiness gate — separate from classification confidence."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.etl.field_mapper import MappingPlan, _REQUIRED_FIELDS
from app.services.etl.row_meaning import RowMeaning
from app.services.etl.types import ColumnMappingDetail, IngestionQuestion

CONFIRMATION_THRESHOLD = 0.75
MIN_COVERAGE_SCORE = 0.5


@dataclass
class AnalysisReadiness:
    ready: bool
    score: float
    blocking_reasons: list[str] = field(default_factory=list)
    required_questions: list[str] = field(default_factory=list)
    usable_row_count: int = 0
    rejected_row_count: int = 0

    def to_dict(self) -> dict:
        return {
            "ready": self.ready,
            "score": round(self.score, 3),
            "blocking_reasons": self.blocking_reasons,
            "required_questions": self.required_questions,
            "usable_row_count": self.usable_row_count,
            "rejected_row_count": self.rejected_row_count,
        }


def compute_analysis_readiness(
    *,
    report_type: str,
    row_count: int,
    mapping_plan: MappingPlan,
    column_mappings: list[ColumnMappingDetail],
    questions: list[IngestionQuestion],
    row_meaning: RowMeaning,
    mapping_answers: dict[str, str] | None = None,
    user_confirmed_mappings: bool = False,
) -> AnalysisReadiness:
    answers = mapping_answers or {}
    blocking: list[str] = []
    required_q_ids: list[str] = []

    for q in questions:
        if q.required_before_analysis and not answers.get(q.id):
            required_q_ids.append(q.id)
            blocking.append(q.reason or q.question)

    if row_meaning.needs_confirmation():
        blocking.append("Row meaning needs user confirmation")
        required_q_ids.append("row_meaning")

    required_fields = list(_REQUIRED_FIELDS.get(report_type, []))
    if report_type == "gl_trial_balance":
        required_fields = ["account_id"]
        if mapping_plan.amount_strategy in ("needs_user_choice", ""):
            if not answers.get("gl_amount_semantics"):
                blocking.append("Amount strategy not chosen")
                required_q_ids.append("gl_amount_semantics")

    for req in required_fields:
        fm = mapping_plan.field_mapping.get(req)
        if not fm or (not fm.source and fm.strategy == "single_column"):
            blocking.append(f"Missing required field: {req}")

    for cm in column_mappings:
        if cm.needs_user_confirmation and not user_confirmed_mappings:
            if cm.canonical_field and cm.source_column:
                blocking.append(f"Confirm mapping: {cm.source_column} → {cm.canonical_field}")

    usable = row_count
    rejected = 0
    if required_fields:
        mapped_required = sum(
            1
            for req in required_fields
            if mapping_plan.field_mapping.get(req)
            and (
                mapping_plan.field_mapping[req].source
                or mapping_plan.field_mapping[req].strategy != "single_column"
            )
        )
        field_ratio = mapped_required / len(required_fields)
    else:
        field_ratio = 0.8

    req_questions = [q for q in questions if q.required_before_analysis]
    if req_questions:
        answered = sum(1 for q in req_questions if answers.get(q.id))
        question_ratio = answered / len(req_questions)
    else:
        question_ratio = 1.0

    row_meaning_ratio = 1.0 if not row_meaning.needs_confirmation() else 0.4

    confirm_penalty = (
        0.0
        if not any(cm.needs_user_confirmation and not user_confirmed_mappings for cm in column_mappings)
        else 0.2
    )

    score = max(
        0.0,
        min(
            1.0,
            field_ratio * 0.35 + question_ratio * 0.35 + row_meaning_ratio * 0.25 - confirm_penalty,
        ),
    )

    if report_type == "gl_trial_balance" and not answers.get("gl_amount_semantics"):
        score = min(score, 0.45)

    ready = len(blocking) == 0 and score >= MIN_COVERAGE_SCORE

    return AnalysisReadiness(
        ready=ready,
        score=score,
        blocking_reasons=blocking,
        required_questions=list(dict.fromkeys(required_q_ids)),
        usable_row_count=usable,
        rejected_row_count=rejected,
    )
