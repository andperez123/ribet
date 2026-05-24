import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    erp_family: Mapped[str] = mapped_column(String(50), default="jobboss")
    portfolio_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    jobs: Mapped[list["IngestJob"]] = relationship(back_populates="organization")


class IngestJob(Base):
    __tablename__ = "ingest_jobs"
    __table_args__ = (Index("ix_ingest_jobs_org_status", "org_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    errors: Mapped[list | None] = mapped_column(JSONB, default=list)
    report_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    report_type: Mapped[str | None] = mapped_column(String(64))
    sector: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organization: Mapped["Organization"] = relationship(back_populates="jobs")


class OrgProgress(Base):
    __tablename__ = "org_progress"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), primary_key=True
    )
    sectors_covered: Mapped[dict] = mapped_column(JSONB, default=dict)
    unlocked_capabilities: Mapped[list] = mapped_column(JSONB, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OperationalFinding(Base):
    __tablename__ = "operational_findings"
    __table_args__ = (
        Index("ix_findings_org_severity", "org_id", "severity", "detected_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ingest_jobs.id"))
    report_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("operational_reports.id"))
    finding_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    business_impact: Mapped[str] = mapped_column(String(64), nullable=False)
    department: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    suggested_action: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HealthSnapshot(Base):
    __tablename__ = "health_snapshots"
    __table_args__ = (Index("ix_health_org_computed", "org_id", "computed_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    report_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("operational_reports.id"))
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    components: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OperationalMemory(Base):
    __tablename__ = "operational_memory"
    __table_args__ = (Index("ix_memory_org_fingerprint", "org_id", "fingerprint", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    finding_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    severity_peak: Mapped[str] = mapped_column(String(32), default="medium")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class OperationalReport(Base):
    __tablename__ = "operational_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    job_ids: Mapped[list] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    executive_summary: Mapped[list] = mapped_column(JSONB, default=list)
    financial_findings: Mapped[list] = mapped_column(JSONB, default=list)
    operational_findings: Mapped[list] = mapped_column(JSONB, default=list)
    risk_areas: Mapped[list] = mapped_column(JSONB, default=list)
    suggested_actions: Mapped[list] = mapped_column(JSONB, default=list)
    trend_snapshot: Mapped[list] = mapped_column(JSONB, default=list)
    health_score: Mapped[int] = mapped_column(Integer, default=0)
    health_status: Mapped[str] = mapped_column(String(32), default="Stable")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductEvent(Base):
    __tablename__ = "product_events"
    __table_args__ = (Index("ix_product_events_type_created", "event_type", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ingest_jobs.id"))
    report_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("operational_reports.id"))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BenchmarkCohort(Base):
    __tablename__ = "benchmark_cohorts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    criteria: Mapped[dict] = mapped_column(JSONB, default=dict)


class BenchmarkMetric(Base):
    __tablename__ = "benchmark_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cohort_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("benchmark_cohorts.id"))
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    p25: Mapped[float | None] = mapped_column(Float)
    p50: Mapped[float | None] = mapped_column(Float)
    p75: Mapped[float | None] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OrgBenchmarkEligibility(Base):
    __tablename__ = "org_benchmark_eligibility"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), primary_key=True)
    cohort_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("benchmark_cohorts.id"), primary_key=True)
    opted_in: Mapped[bool] = mapped_column(Boolean, default=False)


# Normalized domain tables
class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (Index("ix_customers_org", "org_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    customer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(512))
    source_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class Vendor(Base):
    __tablename__ = "vendors"
    __table_args__ = (Index("ix_vendors_org", "org_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    vendor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(512))
    balance: Mapped[float | None] = mapped_column(Float)
    source_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class GlTransaction(Base):
    __tablename__ = "gl_transactions"
    __table_args__ = (Index("ix_gl_org", "org_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    transaction_id: Mapped[str] = mapped_column(String(128))
    account_id: Mapped[str] = mapped_column(String(128))
    account_name: Mapped[str | None] = mapped_column(String(512))
    amount: Mapped[float] = mapped_column(Float, default=0)
    posted_at: Mapped[str | None] = mapped_column(String(32))
    source_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (Index("ix_invoices_org", "org_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    invoice_id: Mapped[str] = mapped_column(String(128))
    customer_id: Mapped[str] = mapped_column(String(128))
    amount: Mapped[float] = mapped_column(Float, default=0)
    due_date: Mapped[str | None] = mapped_column(String(32))
    days_overdue: Mapped[int | None] = mapped_column(Integer)
    aging_bucket: Mapped[str | None] = mapped_column(String(32))
    source_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    __table_args__ = (Index("ix_inventory_org", "org_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    item_id: Mapped[str] = mapped_column(String(128))
    sku: Mapped[str] = mapped_column(String(128))
    quantity: Mapped[float] = mapped_column(Float, default=0)
    gl_account: Mapped[str | None] = mapped_column(String(128))
    source_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
