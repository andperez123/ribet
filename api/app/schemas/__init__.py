from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.insights import (
    AnalysisMetadataOut,
    DataCoverageOut,
    DataDigestOut,
    DomainInsightOut,
)


UploadStatus = Literal["pending", "processing", "done", "error", "needs_review"]
Severity = Literal["low", "medium", "high", "critical"]


class JobErrorOut(BaseModel):
    code: str
    message: str
    hint: str | None = None
    detail: str | None = None


class UploadJob(BaseModel):
    id: UUID
    status: UploadStatus
    file_name: str
    sector: str | None = None
    errors: list[JobErrorOut] = Field(default_factory=list)
    report_id: UUID | None = None
    mapping_status: str | None = None
    mapping_confidence: float | None = None
    duplicate_of_job_id: UUID | None = None
    created_at: str | None = None
    updated_at: str | None = None
    intake_metadata: dict | None = None


class SectorStatus(BaseModel):
    id: str
    label: str
    covered: bool
    count: int = 0
    last_upload_at: str | None = None
    last_report_type: str | None = None


class CapabilityStatus(BaseModel):
    id: str
    name: str
    description: str
    unlocked: bool
    requirement: str | None = None


class OrgProgressOut(BaseModel):
    sectors: list[SectorStatus]
    capabilities: list[CapabilityStatus]
    coverage_count: int


class CoverageItemOut(BaseModel):
    key: str
    label: str
    sector: str
    covered: bool
    uploadable: bool


class ConfidenceBreakdownOut(BaseModel):
    key: str
    label: str
    weight: int
    covered: bool


class NextUploadOut(BaseModel):
    key: str
    label: str
    confidence_if_uploaded: int


class DataGapOut(BaseModel):
    id: str
    gap_type: str
    reason: str
    recommended_uploads: list[str] = Field(default_factory=list)
    requested_report_types: list[str] = Field(default_factory=list)
    requested_sector: str | None = None
    confidence_if_uploaded: int | None = None
    priority: str = "medium"
    status: str = "open"


class OrgCoverageOut(BaseModel):
    understood: list[CoverageItemOut]
    needed: list[CoverageItemOut]
    analysis_confidence: int
    confidence_breakdown: list[ConfidenceBreakdownOut]
    next_upload: NextUploadOut | None = None
    gaps: list[DataGapOut] = Field(default_factory=list)


class UploadJobsResponse(BaseModel):
    jobs: list[UploadJob]


class DemoOrgResponse(BaseModel):
    org_id: UUID
    org_name: str
    jobs: list[UploadJob]


class FindingOut(BaseModel):
    id: UUID
    finding_type: str
    title: str
    detail: str
    severity: str
    confidence: float
    business_impact: str
    department: str
    category: str
    suggested_action: str | None = None
    narrative: str | None = None
    recommendation: str | None = None
    detected_at: str

    model_config = {"from_attributes": True}


class HealthScore(BaseModel):
    score: int
    status: str
    components: dict = Field(default_factory=dict)
    computed_at: str | None = None


class HealthHistory(BaseModel):
    snapshots: list[HealthScore]


class ReportSummary(BaseModel):
    id: UUID
    generated_at: str
    health_score: int
    health_status: str
    finding_count: int = 0


class ReportsListResponse(BaseModel):
    reports: list[ReportSummary]


class OperationalReportOut(BaseModel):
    id: UUID
    org_id: UUID
    executive_summary: list[str]
    financial_findings: list[dict]
    operational_findings: list[dict]
    risk_areas: list[dict]
    suggested_actions: list[str]
    trend_snapshot: list[str]
    health_score: int
    health_status: str
    generated_at: str
    data_digest: DataDigestOut = Field(default_factory=DataDigestOut)
    domain_insights: list[DomainInsightOut] = Field(default_factory=list)
    data_coverage: DataCoverageOut = Field(default_factory=DataCoverageOut)
    analysis_metadata: AnalysisMetadataOut = Field(default_factory=AnalysisMetadataOut)
    analyst_summary: str | None = None
    management_questions: list[str] = Field(default_factory=list)
    period_label: str | None = None
    improvement_notes: list[dict] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class WeeklyBrief(BaseModel):
    org_id: UUID
    period: str
    sections: dict[str, list[str]]
