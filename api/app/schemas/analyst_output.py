from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ANALYST_OUTPUT_SCHEMA_VERSION = "analyst_output.v1"
PROMPT_VERSION = "ai_analyst.v1"


class TopRisk(BaseModel):
    rank: int
    title: str
    impact: Literal["high", "medium", "low"]
    finding_ids: list[str] = Field(default_factory=list)
    metric_keys: list[str] = Field(default_factory=list)
    narrative: str
    recommended_action: str


class WhatChangedItem(BaseModel):
    metric_key: str
    narrative: str
    finding_ids: list[str] = Field(default_factory=list)


class ManagementQuestion(BaseModel):
    question: str
    context: str
    finding_ids: list[str] = Field(default_factory=list)


class RecommendedUpload(BaseModel):
    upload: str
    priority: Literal["high", "medium", "low"] = "medium"
    confidence_lift: float = 0.0
    rationale: str
    reason_code: str = ""
    finding_ids: list[str] = Field(default_factory=list)


class ConditionalInsight(BaseModel):
    locked_capability: str
    requires_upload: str
    insight: str
    finding_ids: list[str] = Field(default_factory=list)


class DashboardExplanations(BaseModel):
    ar_risk: str = ""
    cash_flow: str = ""
    inventory: str = ""
    data_quality: str = ""


class DomainInsightsOutput(BaseModel):
    controller: str = ""
    inventory: str = ""
    data_quality: str = ""


class AnalystOutput(BaseModel):
    schema_version: str = ANALYST_OUTPUT_SCHEMA_VERSION
    executive_summary: list[str] = Field(default_factory=list)
    top_risks: list[TopRisk] = Field(default_factory=list)
    what_changed: list[WhatChangedItem] = Field(default_factory=list)
    management_questions: list[ManagementQuestion] = Field(default_factory=list)
    recommended_uploads: list[RecommendedUpload] = Field(default_factory=list)
    dashboard_explanations: DashboardExplanations = Field(default_factory=DashboardExplanations)
    domain_insights: DomainInsightsOutput = Field(default_factory=DomainInsightsOutput)
    confidence_notes: list[str] = Field(default_factory=list)
    conditional_insights: list[ConditionalInsight] = Field(default_factory=list)
    source: Literal["ai", "deterministic_fallback"] = "ai"

    model_config = {"extra": "forbid"}


class VerifyResult(BaseModel):
    passed: bool
    failures: list[str] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict)
