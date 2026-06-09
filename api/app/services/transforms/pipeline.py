"""Transform upload: intake → profile → map → canonical → persist."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import IngestJob, Organization
from app.services.etl.detector import detect_report_type
from app.services.etl.field_mapper import MappingPlan, propose_mapping
from app.services.etl.profiler import profile_dataframe
from app.services.mapping_memory import apply_org_mapping_memory
from app.services.storage import read_upload_to_dataframe
from app.services.transforms.adapters import generic as generic_adapter
from app.services.transforms.adapters import jobboss as jobboss_adapter
from app.services.transforms.normalization.periods import period_from_dataframe
from app.services.transforms.persist import persist_canonical

CONFIDENCE_AUTO_THRESHOLD = 0.75


@dataclass
class TransformResult:
    report_type: str
    period: str
    row_count: int
    status: str = "auto"
    mapping_plan: MappingPlan | None = None
    intake_metadata: dict | None = None
    schema_fingerprint: str | None = None


def _schema_fingerprint(columns: list[str], report_type: str) -> str:
    normalized = "|".join(sorted(c.lower().strip() for c in columns))
    raw = f"{report_type}:{normalized}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _find_duplicate_job(db: Session, org_id: UUID, content_hash: str, exclude_id: UUID) -> UUID | None:
    prior = (
        db.query(IngestJob)
        .filter(
            IngestJob.org_id == org_id,
            IngestJob.content_hash == content_hash,
            IngestJob.id != exclude_id,
            IngestJob.status == "done",
        )
        .order_by(IngestJob.created_at.desc())
        .first()
    )
    return prior.id if prior else None


def transform_upload(
    db: Session,
    org: Organization,
    job: IngestJob,
    filename: str,
    storage_key: str,
) -> TransformResult:
    intake = read_upload_to_dataframe(storage_key, filename)
    df = intake.dataframe
    columns = list(df.columns)
    report_type = detect_report_type(filename, columns, sector_hint=job.sector)
    profiles = profile_dataframe(df)
    plan = propose_mapping(profiles, report_type, columns)
    plan = apply_org_mapping_memory(org, plan, columns)

    extra_samples: dict[str, list[str]] = {}
    for col in plan.unmapped_columns[:25]:
        if col in df.columns:
            extra_samples[col] = [
                str(v).strip()
                for v in df[col].dropna().head(5).tolist()
                if str(v).strip()
            ]
    period = period_from_dataframe(df, column_map=plan.column_map)
    fingerprint = _schema_fingerprint(columns, report_type)

    job.intake_metadata = intake.metadata.to_dict()
    job.detected_period = period
    job.schema_fingerprint = fingerprint
    job.mapping_metadata = {**plan.to_dict(), "extra_column_samples": extra_samples}
    job.mapping_confidence = plan.overall_confidence

    if not job.content_hash:
        from app.services.storage import download_file

        job.content_hash = hashlib.sha256(download_file(storage_key)).hexdigest()
    dup = _find_duplicate_job(db, org.id, job.content_hash, job.id)
    if dup:
        job.duplicate_of_job_id = dup

    if plan.overall_confidence < CONFIDENCE_AUTO_THRESHOLD:
        job.mapping_status = "needs_review"
        job.status = "needs_review"
        db.flush()
        return TransformResult(
            report_type=report_type,
            period=period,
            row_count=0,
            status="needs_review",
            mapping_plan=plan,
            intake_metadata=intake.metadata.to_dict(),
            schema_fingerprint=fingerprint,
        )

    adapter_module = jobboss_adapter if org.erp_family == "jobboss" else generic_adapter
    dataset = adapter_module.dataframe_to_canonical(report_type, df, plan=plan)
    row_count = persist_canonical(db, org.id, job.id, period, dataset)

    job.mapping_status = "auto"
    job.row_count = row_count
    db.flush()

    return TransformResult(
        report_type=report_type,
        period=period,
        row_count=row_count,
        status="auto",
        mapping_plan=plan,
        intake_metadata=intake.metadata.to_dict(),
        schema_fingerprint=fingerprint,
    )
