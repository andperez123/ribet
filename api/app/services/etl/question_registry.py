"""Rule-based ingestion questions derived from classification and mapping gaps."""

from __future__ import annotations

from app.services.etl.classifier import DatasetClassification
from app.services.etl.field_mapper import MappingPlan
from app.services.etl.profiler import DataProfile
from app.services.etl.row_meaning import RowMeaning
from app.services.etl.types import ColumnMappingDetail, IngestionQuestion, QuestionOption


def _tbal_amount_question() -> IngestionQuestion:
    return IngestionQuestion(
        id="gl_amount_semantics",
        question="How should Ribet interpret amount for analysis?",
        reason="Trial balance files have multiple numeric columns — Ribet needs to know which meaning to use.",
        affected_fields=["amount", "amount_strategy"],
        options=[
            QuestionOption(
                value="net_activity",
                label="Period activity",
                description="END_BAL − BEG_BAL (net change for the period)",
                recommended=True,
            ),
            QuestionOption(
                value="ending_balance",
                label="Ending balance",
                description="Use END_BAL as the amount per account",
            ),
            QuestionOption(
                value="debit_credit_activity",
                label="Debit/credit activity",
                description="DEBITS + CREDITS (signed period activity)",
            ),
            QuestionOption(
                value="single_column",
                label="Pick a column",
                description="Manually map a single amount column",
            ),
        ],
    )


def _row_meaning_question(row_meaning: RowMeaning) -> IngestionQuestion:
    return IngestionQuestion(
        id="row_meaning",
        question="What does one row in this file represent?",
        reason="Ribet needs row-level meaning before analysis can run correctly.",
        affected_fields=["row_meaning"],
        options=[QuestionOption(value=o.value, label=o.label) for o in row_meaning.options],
        required_before_analysis=True,
    )


def _unknown_export_questions() -> list[IngestionQuestion]:
    return [
        IngestionQuestion(
            id="primary_entity_column",
            question="Which column is the primary entity (customer, vendor, part, account, etc.)?",
            reason="Ribet could not confidently classify this export type.",
            affected_fields=["entity"],
            options=[],
            required_before_analysis=True,
        ),
        IngestionQuestion(
            id="amount_or_quantity_column",
            question="Which column is the amount, quantity, or primary measure?",
            reason="Analysis requires a numeric measure column.",
            affected_fields=["amount", "quantity"],
            options=[],
            required_before_analysis=True,
        ),
    ]


def _negative_balance_question() -> IngestionQuestion:
    return IngestionQuestion(
        id="negative_balances_are_credits",
        question="Are negative balances credits?",
        reason="This file contains negative monetary values that may represent credits.",
        affected_fields=["amount"],
        options=[
            QuestionOption(value="yes", label="Yes — treat negatives as credits"),
            QuestionOption(value="no", label="No — keep signed values as-is"),
        ],
        required_before_analysis=False,
    )


def generate_questions(
    classification: DatasetClassification,
    mapping_plan: MappingPlan,
    column_mappings: list[ColumnMappingDetail],
    row_meaning: RowMeaning,
    data_profile: DataProfile,
    mapping_answers: dict[str, str] | None = None,
) -> list[IngestionQuestion]:
    answers = mapping_answers or {}
    questions: list[IngestionQuestion] = []

    if row_meaning.needs_confirmation() and not answers.get("row_meaning"):
        questions.append(_row_meaning_question(row_meaning))

    if classification.likely_type == "gl_trial_balance":
        if mapping_plan.amount_strategy in ("needs_user_choice", "single_column") and not answers.get(
            "gl_amount_semantics"
        ):
            questions.append(_tbal_amount_question())

    if classification.likely_type == "unknown_operational_export":
        questions.extend(_unknown_export_questions())

    if classification.likely_type == "ar_aging":
        for col in data_profile.detected_money_columns:
            for row in data_profile.sample_rows:
                val = row.get(col, "")
                try:
                    if val and float(str(val).replace(",", "")) < 0:
                        questions.append(_negative_balance_question())
                        break
                except ValueError:
                    pass
            else:
                continue
            break

    for cm in column_mappings:
        if cm.needs_user_confirmation and cm.canonical_field:
            qid = f"confirm_mapping_{cm.source_column}"
            if not answers.get(qid):
                questions.append(
                    IngestionQuestion(
                        id=qid,
                        question=f"Confirm mapping: {cm.source_column} → {cm.canonical_field}?",
                        reason=cm.reason,
                        affected_fields=[cm.canonical_field] if cm.canonical_field else [],
                        options=[
                            QuestionOption(value="yes", label="Yes, use this mapping"),
                            QuestionOption(value="no", label="No, I'll choose a different column"),
                        ],
                        required_before_analysis=True,
                    )
                )

    required = {
        "ar_aging": ["customer_name"],
        "ap_aging": ["vendor_name"],
        "gl_detail": ["account_id", "amount"],
        "inventory": ["sku"],
    }
    for req in required.get(classification.likely_type, []):
        fm = mapping_plan.field_mapping.get(req)
        if not fm or (not fm.source and fm.strategy == "single_column"):
            qid = f"pick_column_{req}"
            if not answers.get(qid):
                questions.append(
                    IngestionQuestion(
                        id=qid,
                        question=f"Which column is {req.replace('_', ' ')}?",
                        reason=f"Required field '{req}' was not auto-detected.",
                        affected_fields=[req],
                        options=[],
                        required_before_analysis=True,
                    )
                )

    return questions
