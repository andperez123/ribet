from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


UploadStatus = Literal["pending", "processing", "done", "error"]
Severity = Literal["low", "medium", "high", "critical"]


class UploadJob(BaseModel):
    id: UUID
    status: UploadStatus
    file_name: str
    sector: str | None = None
    errors: list[str] = Field(default_factory=list)
    report_id: UUID | None = None
    created_at: str | None = None
    updated_at: str | None = None


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


class UploadJobsResponse(BaseModel):
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
    detected_at: str

    model_config = {"from_attributes": True}


class HealthScore(BaseModel):
    score: int
    status: str
    components: dict = Field(default_factory=dict)
    computed_at: str | None = None


class HealthHistory(BaseModel):
    snapshots: list[HealthScore]


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

    model_config = {"from_attributes": True}


class WeeklyBrief(BaseModel):
    org_id: UUID
    period: str
    sections: dict[str, list[str]]
