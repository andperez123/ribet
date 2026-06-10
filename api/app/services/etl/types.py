"""Shared ETL datatypes — avoids circular imports between readiness and question_registry."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ColumnMappingDetail:
    source_column: str
    canonical_field: str | None
    confidence: float
    reason: str
    needs_user_confirmation: bool

    def to_dict(self) -> dict:
        return {
            "source_column": self.source_column,
            "canonical_field": self.canonical_field,
            "confidence": round(self.confidence, 3),
            "reason": self.reason,
            "needs_user_confirmation": self.needs_user_confirmation,
        }


@dataclass
class QuestionOption:
    value: str
    label: str
    description: str = ""
    recommended: bool = False

    def to_dict(self) -> dict:
        d: dict = {"value": self.value, "label": self.label, "description": self.description}
        if self.recommended:
            d["recommended"] = True
        return d


@dataclass
class IngestionQuestion:
    id: str
    question: str
    reason: str
    affected_fields: list[str] = field(default_factory=list)
    options: list[QuestionOption] = field(default_factory=list)
    required_before_analysis: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "reason": self.reason,
            "affected_fields": self.affected_fields,
            "options": [o.to_dict() for o in self.options],
            "required_before_analysis": self.required_before_analysis,
        }
