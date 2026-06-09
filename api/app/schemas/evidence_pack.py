from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


EVIDENCE_PACK_SCHEMA_VERSION = "evidence_pack.v1"


class EvidencePackConfidenceComponents(BaseModel):
    coverage_completeness: float
    mapping_quality: float
    cross_domain_joinability: float
    temporal_depth: float


class EvidencePackConfidence(BaseModel):
    legacy_score: int
    normalized_score: float
    components: EvidencePackConfidenceComponents


class EvidencePackCoverage(BaseModel):
    sectors: dict[str, bool]
    domains: dict[str, bool]
    sectors_count: int
    sectors_total: int = 4


class EvidencePackHealthComponents(BaseModel):
    ar_risk: int | None = None
    cash_flow: int | None = None
    inventory: int | None = None
    data_quality: int | None = None


class EvidencePackHealth(BaseModel):
    score: int
    status: str
    components: EvidencePackHealthComponents
    prior_score: int | None = None
    delta: int | None = None


class EvidencePackEntity(BaseModel):
    name: str
    amount: float
    pct_of_total: float | None = None


class EvidencePackTopEntities(BaseModel):
    customers: list[EvidencePackEntity] = Field(default_factory=list)
    vendors: list[EvidencePackEntity] = Field(default_factory=list)
    inventory_items: list[EvidencePackEntity] = Field(default_factory=list)


class EvidencePackFinding(BaseModel):
    finding_id: str
    finding_instance_id: str
    title: str
    severity: str
    domain: str
    tags: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    source_metric_keys: list[str] = Field(default_factory=list)
    deterministic_action: str | None = None


class EvidencePackTrendDelta(BaseModel):
    metric: str
    prior: float | int | None = None
    current: float | int | None = None
    delta: float | int | None = None
    direction: str | None = None


class EvidencePackDataGap(BaseModel):
    upload: str
    confidence_lift: float
    reason_code: str
    priority: str = "medium"


class EvidencePackDataQuality(BaseModel):
    mapping_warnings: list[str] = Field(default_factory=list)
    failed_uploads: list[dict[str, str]] = Field(default_factory=list)
    low_confidence_mappings: list[dict[str, Any]] = Field(default_factory=list)


class EvidencePackAnalysisBoundaries(BaseModel):
    can_conclude: list[str] = Field(default_factory=list)
    cannot_conclude: list[str] = Field(default_factory=list)


class EvidencePackMemory(BaseModel):
    enabled: bool = False
    recurring_findings: list[dict[str, Any]] = Field(default_factory=list)


class EvidencePackLockedCapability(BaseModel):
    capability: str
    requires_sector: str | None = None
    requires_sectors: int | None = None


class EvidencePack(BaseModel):
    schema_version: str = EVIDENCE_PACK_SCHEMA_VERSION
    agent_ready: bool = True
    agent_input_type: str = EVIDENCE_PACK_SCHEMA_VERSION
    raw_data_included: bool = False
    org_id: str
    org_name: str
    period: str
    generated_at: datetime
    prior_period: str | None = None
    coverage: EvidencePackCoverage
    confidence: EvidencePackConfidence
    health: EvidencePackHealth
    metrics: dict[str, Any]
    top_entities: EvidencePackTopEntities
    findings: list[EvidencePackFinding]
    trend_deltas: list[EvidencePackTrendDelta] = Field(default_factory=list)
    data_gaps: list[EvidencePackDataGap] = Field(default_factory=list)
    data_quality: EvidencePackDataQuality = Field(default_factory=EvidencePackDataQuality)
    analysis_boundaries: EvidencePackAnalysisBoundaries = Field(
        default_factory=EvidencePackAnalysisBoundaries
    )
    memory: EvidencePackMemory = Field(default_factory=EvidencePackMemory)
    locked_capabilities: list[EvidencePackLockedCapability] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
