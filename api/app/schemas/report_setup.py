from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

CONTEXT_SCHEMA_VERSION = 1


class SetupWarningOut(BaseModel):
    code: str
    message: str


class ReportSourceJobOut(BaseModel):
    id: UUID
    file_name: str
    report_type: str | None = None
    detected_period: str | None = None
    row_count: int | None = None
    status: str
    report_id: UUID | None = None
    mapping_confidence: float | None = None
    created_at: str | None = None
    report_type_label: str | None = None


class ReportSetupDraftOut(BaseModel):
    context_schema_version: int = CONTEXT_SCHEMA_VERSION
    source_job_ids: list[UUID] = Field(default_factory=list)
    manual_notes: str | None = None
    excluded_finding_ids: list[str] = Field(default_factory=list)
    evidence_overrides: dict = Field(default_factory=dict)
    narrative_overrides: dict = Field(default_factory=dict)


class BlockedAnalysisOut(BaseModel):
    analysis_name: str
    reason_code: str
    reason: str
    requires_uploads: list[str] = Field(default_factory=list)


class SetupPreviewOut(BaseModel):
    domains_covered: list[str] = Field(default_factory=list)
    sectors_covered: list[str] = Field(default_factory=list)
    analysis_confidence: int = 0
    blocked_analyses: list[BlockedAnalysisOut] = Field(default_factory=list)
    warnings: list[SetupWarningOut] = Field(default_factory=list)


class ReportSetupGetOut(BaseModel):
    draft: ReportSetupDraftOut
    available_jobs: list[ReportSourceJobOut]
    warnings: list[SetupWarningOut] = Field(default_factory=list)
    preview: SetupPreviewOut | None = None


class ReportSetupPutIn(BaseModel):
    source_job_ids: list[UUID] | None = None
    manual_notes: str | None = None
    excluded_finding_ids: list[str] | None = None
    evidence_overrides: dict | None = None
    narrative_overrides: dict | None = None


class RegenerateRequest(BaseModel):
    source_job_ids: list[UUID] | None = None
    manual_notes: str | None = None
    excluded_finding_ids: list[str] | None = None
    evidence_overrides: dict | None = None
    narrative_overrides: dict | None = None
    mode: Literal["full", "ai_only"] = "full"


class ReportGenerationSnapshotOut(BaseModel):
    context_schema_version: int
    source_job_ids: list[UUID]
    period_label: str | None = None
    domains: list[str] | None = None
    submitted_at: str
    submitted_by_user_id: UUID | None = None
    source_context_hash: str
    regenerate_mode: str = "full"
    manual_notes: str | None = None
    excluded_finding_ids: list[str] = Field(default_factory=list)
    evidence_overrides: dict = Field(default_factory=dict)
    narrative_overrides: dict = Field(default_factory=dict)


class ReportSetupSnapshotOut(BaseModel):
    snapshot: ReportGenerationSnapshotOut
    sources: list[ReportSourceJobOut]


class ReportPatchIn(BaseModel):
    executive_summary: list[str] | None = None
    management_questions: list[str] | None = None
    narrative_overrides: dict | None = None
