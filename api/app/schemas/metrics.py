from pydantic import BaseModel, Field


class TotalsBlock(BaseModel):
    orgs: int = 0
    uploads: int = 0
    reports: int = 0
    findings: int = 0
    active_orgs_30d: int = 0


class ActivationBlock(BaseModel):
    rate_pct: float = 0.0
    orgs_with_report: int = 0
    median_time_to_first_report_hours: float | None = None


class EngagementBlock(BaseModel):
    upload_success_rate_pct: float = 0.0
    report_yield_rate_pct: float = 0.0
    avg_sectors_per_active_org: float = 0.0
    repeat_upload_rate_pct: float = 0.0
    avg_findings_per_report: float = 0.0


class WeeklyBucket(BaseModel):
    week_start: str
    uploads: int = 0
    reports: int = 0
    new_orgs: int = 0
    cumulative_reports: int = 0


class OrgMetricsRow(BaseModel):
    org_id: str
    name: str
    created_at: str
    uploads: int = 0
    reports: int = 0
    sectors_covered: int = 0
    findings: int = 0
    last_upload_at: str | None = None
    last_report_at: str | None = None
    health_score: int | None = None


class AdminMetricsOut(BaseModel):
    generated_at: str
    totals: TotalsBlock
    activation: ActivationBlock
    engagement: EngagementBlock
    weekly: list[WeeklyBucket] = Field(default_factory=list)
    orgs: list[OrgMetricsRow] = Field(default_factory=list)
