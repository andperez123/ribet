from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

JsonColumn = JSON().with_variant(JSONB(), "postgresql")

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    erp_family: Mapped[str] = mapped_column(String(50), default="jobboss")
    portfolio_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    clerk_org_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    email_recipients: Mapped[Optional[list]] = mapped_column(JsonColumn, default=list)
    mapping_memory: Mapped[Optional[dict]] = mapped_column(JsonColumn, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    jobs: Mapped[list["IngestJob"]] = relationship(back_populates="organization")


class IngestJob(Base):
    __tablename__ = "ingest_jobs"
    __table_args__ = (Index("ix_ingest_jobs_org_status", "org_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128))
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    errors: Mapped[Optional[list]] = mapped_column(JsonColumn, default=list)
    report_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    report_type: Mapped[Optional[str]] = mapped_column(String(64))
    sector: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    consent_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    user_description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    schema_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    detected_period: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mapping_metadata: Mapped[Optional[dict]] = mapped_column(JsonColumn, nullable=True)
    mapping_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mapping_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    intake_metadata: Mapped[Optional[dict]] = mapped_column(JsonColumn, nullable=True)
    pipeline_stage: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    duplicate_of_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organization: Mapped["Organization"] = relationship(back_populates="jobs")


class OrgProgress(Base):
    __tablename__ = "org_progress"

    org_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), primary_key=True
    )
    sectors_covered: Mapped[dict] = mapped_column(JsonColumn, default=dict)
    unlocked_capabilities: Mapped[list] = mapped_column(JsonColumn, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OperationalFinding(Base):
    __tablename__ = "operational_findings"
    __table_args__ = (
        Index("ix_findings_org_severity", "org_id", "severity", "detected_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), nullable=False)
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("ingest_jobs.id"))
    report_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("operational_reports.id"))
    finding_type: Mapped[str] = mapped_column(String(64), nullable=False)
    finding_id: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    finding_instance_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    business_impact: Mapped[str] = mapped_column(String(64), nullable=False)
    department: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    suggested_action: Mapped[Optional[str]] = mapped_column(Text)
    narrative: Mapped[Optional[str]] = mapped_column(Text)
    recommendation: Mapped[Optional[str]] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OperationalSnapshot(Base):
    __tablename__ = "operational_snapshots"
    __table_args__ = (Index("ix_op_snapshots_org_period", "org_id", "period", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)
    cash_position: Mapped[Optional[float]] = mapped_column(Float)
    ar_over_90_pct: Mapped[Optional[float]] = mapped_column(Float)
    ar_total: Mapped[Optional[float]] = mapped_column(Float)
    ap_total: Mapped[Optional[float]] = mapped_column(Float)
    inventory_value: Mapped[Optional[float]] = mapped_column(Float)
    inventory_turns: Mapped[Optional[float]] = mapped_column(Float)
    vendor_concentration: Mapped[Optional[float]] = mapped_column(Float)
    health_score: Mapped[int] = mapped_column(Integer, default=0)
    health_status: Mapped[str] = mapped_column(String(32), default="Stable")
    metrics: Mapped[dict] = mapped_column(JsonColumn, default=dict)
    source_job_ids: Mapped[list] = mapped_column(JsonColumn, default=list)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HealthSnapshot(Base):
    __tablename__ = "health_snapshots"
    __table_args__ = (Index("ix_health_org_computed", "org_id", "computed_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), nullable=False)
    report_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("operational_reports.id"))
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    components: Mapped[dict] = mapped_column(JsonColumn, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JsonColumn, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OperationalMemory(Base):
    __tablename__ = "operational_memory"
    __table_args__ = (Index("ix_memory_org_fingerprint", "org_id", "fingerprint", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    finding_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    severity_peak: Mapped[str] = mapped_column(String(32), default="medium")
    metadata_: Mapped[dict] = mapped_column("metadata", JsonColumn, default=dict)


class OperationalReport(Base):
    __tablename__ = "operational_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), nullable=False)
    job_ids: Mapped[list] = mapped_column(JsonColumn, default=list)
    executive_summary: Mapped[list] = mapped_column(JsonColumn, default=list)
    financial_findings: Mapped[list] = mapped_column(JsonColumn, default=list)
    operational_findings: Mapped[list] = mapped_column(JsonColumn, default=list)
    risk_areas: Mapped[list] = mapped_column(JsonColumn, default=list)
    suggested_actions: Mapped[list] = mapped_column(JsonColumn, default=list)
    trend_snapshot: Mapped[list] = mapped_column(JsonColumn, default=list)
    health_score: Mapped[int] = mapped_column(Integer, default=0)
    health_status: Mapped[str] = mapped_column(String(32), default="Stable")
    data_digest: Mapped[Optional[dict]] = mapped_column(JsonColumn, nullable=True)
    domain_insights: Mapped[Optional[list]] = mapped_column(JsonColumn, nullable=True)
    data_coverage: Mapped[Optional[dict]] = mapped_column(JsonColumn, nullable=True)
    analysis_metadata: Mapped[Optional[dict]] = mapped_column(JsonColumn, nullable=True)
    analyst_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    management_questions: Mapped[Optional[list]] = mapped_column(JsonColumn, nullable=True)
    period_label: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    improvement_notes: Mapped[Optional[list]] = mapped_column(JsonColumn, nullable=True)
    report_contract: Mapped[Optional[dict]] = mapped_column(JsonColumn, nullable=True)
    generation_context: Mapped[Optional[dict]] = mapped_column(JsonColumn, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_jobs: Mapped[list["OperationalReportSourceJob"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )


class ReportContextDraft(Base):
    __tablename__ = "report_context_drafts"

    org_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), primary_key=True
    )
    context_schema_version: Mapped[int] = mapped_column(Integer, default=1)
    source_job_ids: Mapped[list] = mapped_column(JsonColumn, default=list)
    manual_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    excluded_finding_ids: Mapped[list] = mapped_column(JsonColumn, default=list)
    evidence_overrides: Mapped[dict] = mapped_column(JsonColumn, default=dict)
    narrative_overrides: Mapped[dict] = mapped_column(JsonColumn, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OperationalReportSourceJob(Base):
    __tablename__ = "operational_report_source_jobs"

    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("operational_reports.id", ondelete="CASCADE"),
        primary_key=True,
    )
    ingest_job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("ingest_jobs.id"), primary_key=True
    )
    included_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    report: Mapped["OperationalReport"] = relationship(back_populates="source_jobs")
    ingest_job: Mapped["IngestJob"] = relationship()


class EvidencePackRecord(Base):
    __tablename__ = "evidence_packs"
    __table_args__ = (Index("ix_evidence_packs_report", "report_id", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("operational_reports.id", ondelete="CASCADE"), nullable=False
    )
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), nullable=False)
    period_label: Mapped[str] = mapped_column(String(16), nullable=False)
    pack: Mapped[dict] = mapped_column(JsonColumn, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), default="evidence_pack.v1")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReportNarrative(Base):
    __tablename__ = "report_narratives"
    __table_args__ = (Index("ix_report_narratives_report", "report_id", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("operational_reports.id", ondelete="CASCADE"), nullable=False
    )
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), nullable=False)
    output: Mapped[dict] = mapped_column(JsonColumn, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), default="analyst_output.v1")
    prompt_version: Mapped[str] = mapped_column(String(32), default="ai_analyst.v1")
    verification_status: Mapped[str] = mapped_column(String(16), default="pending")
    verification_failures: Mapped[Optional[list]] = mapped_column(JsonColumn, nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[Optional[dict]] = mapped_column(JsonColumn, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="ai")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DataSeries(Base):
    __tablename__ = "data_series"
    __table_args__ = (
        Index("ix_data_series_org_fingerprint", "org_id", "schema_fingerprint", "report_type", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), nullable=False)
    report_type: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SeriesSnapshot(Base):
    __tablename__ = "series_snapshots"
    __table_args__ = (Index("ix_series_snapshots_series_at", "series_id", "snapshot_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    series_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("data_series.id"), nullable=False)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("ingest_jobs.id"), nullable=True)
    report_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("operational_reports.id"), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    kpi_summary: Mapped[dict] = mapped_column(JsonColumn, default=dict)
    improvement_notes: Mapped[list] = mapped_column(JsonColumn, default=list)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductEvent(Base):
    __tablename__ = "product_events"
    __table_args__ = (Index("ix_product_events_type_created", "event_type", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("organizations.id"))
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("ingest_jobs.id"))
    report_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("operational_reports.id"))
    metadata_: Mapped[dict] = mapped_column("metadata", JsonColumn, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DataGapRequest(Base):
    __tablename__ = "data_gap_requests"
    __table_args__ = (Index("ix_data_gap_org_status", "org_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), nullable=False)
    gap_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_uploads: Mapped[list] = mapped_column(JsonColumn, default=list)
    requested_report_types: Mapped[list] = mapped_column(JsonColumn, default=list)
    requested_sector: Mapped[Optional[str]] = mapped_column(String(32))
    confidence_if_uploaded: Mapped[Optional[int]] = mapped_column(Integer)
    priority: Mapped[str] = mapped_column(String(16), default="medium")
    status: Mapped[str] = mapped_column(String(16), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BenchmarkCohort(Base):
    __tablename__ = "benchmark_cohorts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    criteria: Mapped[dict] = mapped_column(JsonColumn, default=dict)


class BenchmarkMetric(Base):
    __tablename__ = "benchmark_metrics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    cohort_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("benchmark_cohorts.id"))
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    p25: Mapped[Optional[float]] = mapped_column(Float)
    p50: Mapped[Optional[float]] = mapped_column(Float)
    p75: Mapped[Optional[float]] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OrgBenchmarkEligibility(Base):
    __tablename__ = "org_benchmark_eligibility"

    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"), primary_key=True)
    cohort_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("benchmark_cohorts.id"), primary_key=True)
    opted_in: Mapped[bool] = mapped_column(Boolean, default=False)


# Normalized domain tables
class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_org", "org_id"),
        Index("ix_customers_org_cust", "org_id", "customer_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"))
    customer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(512))
    source_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)


class Vendor(Base):
    __tablename__ = "vendors"
    __table_args__ = (
        Index("ix_vendors_org", "org_id"),
        Index("ix_vendors_org_period", "org_id", "period_label"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"))
    vendor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(512))
    balance: Mapped[Optional[float]] = mapped_column(Float)
    days_overdue: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    aging_bucket: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    bucket_breakdown: Mapped[Optional[dict]] = mapped_column(JsonColumn, nullable=True)
    period_label: Mapped[str] = mapped_column(String(16), default="unknown")
    source_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)


class GlTransaction(Base):
    __tablename__ = "gl_transactions"
    __table_args__ = (
        Index("ix_gl_org", "org_id"),
        Index("ix_gl_org_period", "org_id", "period_label"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"))
    transaction_id: Mapped[str] = mapped_column(String(128))
    account_id: Mapped[str] = mapped_column(String(128))
    account_name: Mapped[Optional[str]] = mapped_column(String(512))
    amount: Mapped[float] = mapped_column(Float, default=0)
    posted_at: Mapped[Optional[str]] = mapped_column(String(32))
    period_label: Mapped[str] = mapped_column(String(16), default="unknown")
    source_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_org", "org_id"),
        Index("ix_invoices_org_period", "org_id", "period_label"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"))
    invoice_id: Mapped[str] = mapped_column(String(128))
    customer_id: Mapped[str] = mapped_column(String(128))
    amount: Mapped[float] = mapped_column(Float, default=0)
    due_date: Mapped[Optional[str]] = mapped_column(String(32))
    days_overdue: Mapped[Optional[int]] = mapped_column(Integer)
    aging_bucket: Mapped[Optional[str]] = mapped_column(String(32))
    period_label: Mapped[str] = mapped_column(String(16), default="unknown")
    source_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    __table_args__ = (
        Index("ix_inventory_org", "org_id"),
        Index("ix_inventory_org_period", "org_id", "period_label"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"))
    item_id: Mapped[str] = mapped_column(String(128))
    sku: Mapped[str] = mapped_column(String(128))
    quantity: Mapped[float] = mapped_column(Float, default=0)
    gl_account: Mapped[Optional[str]] = mapped_column(String(128))
    period_label: Mapped[str] = mapped_column(String(16), default="unknown")
    source_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (Index("ix_po_org_period", "org_id", "period_label"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"))
    po_id: Mapped[str] = mapped_column(String(128))
    vendor_id: Mapped[str] = mapped_column(String(128))
    vendor_name: Mapped[Optional[str]] = mapped_column(String(512))
    order_date: Mapped[Optional[str]] = mapped_column(String(32))
    promise_date: Mapped[Optional[str]] = mapped_column(String(32))
    due_date: Mapped[Optional[str]] = mapped_column(String(32))
    status: Mapped[Optional[str]] = mapped_column(String(64))
    line_amount: Mapped[float] = mapped_column(Float, default=0)
    open_amount: Mapped[float] = mapped_column(Float, default=0)
    days_late: Mapped[int] = mapped_column(Integer, default=0)
    sku: Mapped[Optional[str]] = mapped_column(String(128))
    qty_ordered: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    qty_received: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    period_label: Mapped[str] = mapped_column(String(16), default="unknown")
    source_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)


class SalesOrder(Base):
    __tablename__ = "sales_orders"
    __table_args__ = (Index("ix_so_org_period", "org_id", "period_label"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("organizations.id"))
    order_id: Mapped[str] = mapped_column(String(128))
    customer_id: Mapped[str] = mapped_column(String(128))
    customer_name: Mapped[Optional[str]] = mapped_column(String(512))
    order_date: Mapped[Optional[str]] = mapped_column(String(32))
    ship_date: Mapped[Optional[str]] = mapped_column(String(32))
    promise_date: Mapped[Optional[str]] = mapped_column(String(32))
    status: Mapped[Optional[str]] = mapped_column(String(64))
    line_amount: Mapped[float] = mapped_column(Float, default=0)
    open_amount: Mapped[float] = mapped_column(Float, default=0)
    days_late: Mapped[int] = mapped_column(Integer, default=0)
    sku: Mapped[Optional[str]] = mapped_column(String(128))
    qty_ordered: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    qty_open: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    period_label: Mapped[str] = mapped_column(String(16), default="unknown")
    source_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
