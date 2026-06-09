"""Mapping review — confirm corrected mappings and resume analysis."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import IngestJob, Organization
from app.services.analysis import run_operational_analysis
from app.services.etl.field_mapper import FieldMapping, MappingPlan
from app.services.storage import read_upload_to_dataframe
from app.services.mapping_memory import save_org_mapping_memory
from app.services.transforms.adapters import generic as generic_adapter
from app.services.transforms.adapters import jobboss as jobboss_adapter
from app.services.transforms.persist import persist_canonical


def _plan_from_job(job: IngestJob) -> MappingPlan:
    meta = job.mapping_metadata or {}
    field_mapping = {}
    for key, val in (meta.get("field_mapping") or {}).items():
        field_mapping[key] = FieldMapping(
            source=val.get("source"),
            confidence=float(val.get("confidence", 0.5)),
            strategy=val.get("strategy", "single_column"),
            sources=val.get("sources") or [],
        )
    return MappingPlan(
        report_type=job.report_type or "unknown",
        field_mapping=field_mapping,
        amount_strategy=meta.get("amount_strategy", "single_column"),
        bucket_columns=meta.get("bucket_columns") or [],
        unmapped_columns=meta.get("unmapped_columns") or [],
        overall_confidence=float(job.mapping_confidence or 0),
        parse_warnings=meta.get("parse_warnings") or [],
        column_map=meta.get("column_map") or {},
    )


def get_mapping_review(db: Session, job: IngestJob) -> dict:
    intake = read_upload_to_dataframe(job.storage_key, job.file_name)
    plan = _plan_from_job(job)
    samples = intake.dataframe.head(5).fillna("").astype(str).to_dict(orient="records")
    from app.services.etl.field_mapper import _REQUIRED_FIELDS

    canonical_fields = sorted(
        set(_REQUIRED_FIELDS.get(plan.report_type, [])) | set(plan.field_mapping.keys())
    )
    return {
        "job_id": str(job.id),
        "status": job.status,
        "mapping_status": job.mapping_status,
        "report_type": job.report_type,
        "mapping_confidence": job.mapping_confidence,
        "mapping": plan.to_dict(),
        "intake_metadata": job.intake_metadata or intake.metadata.to_dict(),
        "sample_rows": samples,
        "columns": list(intake.dataframe.columns),
        "canonical_fields": canonical_fields,
        "unmapped_columns": plan.unmapped_columns,
    }


def confirm_job_mapping(
    db: Session,
    org: Organization,
    job: IngestJob,
    column_map: dict[str, str] | None = None,
) -> IngestJob:
    if job.status not in ("needs_review", "processing"):
        raise ValueError(f"Job cannot be confirmed from status: {job.status}")

    intake = read_upload_to_dataframe(job.storage_key, job.file_name)
    plan = _plan_from_job(job)
    if column_map:
        plan.column_map.update(column_map)
        for orig, canonical in column_map.items():
            if orig and canonical:
                plan.field_mapping[canonical] = FieldMapping(
                    source=orig, confidence=1.0, strategy="single_column"
                )

    report_type = job.report_type or plan.report_type
    period = job.detected_period or "unknown"
    adapter = jobboss_adapter if org.erp_family == "jobboss" else generic_adapter
    dataset = adapter.dataframe_to_canonical(report_type, intake.dataframe, plan=plan)
    row_count = persist_canonical(db, org.id, job.id, period, dataset)

    job.mapping_status = "user_confirmed"
    prior_meta = job.mapping_metadata or {}
    job.mapping_metadata = {
        **plan.to_dict(),
        "extra_column_samples": prior_meta.get("extra_column_samples") or {},
    }
    job.mapping_confidence = max(plan.overall_confidence, 0.85)
    job.row_count = row_count
    job.status = "processing"
    save_org_mapping_memory(org, plan, list(intake.dataframe.columns))
    db.flush()

    analysis = run_operational_analysis(db, org.id, job.id, period=period)
    job.report_id = analysis.report.id
    job.status = "done"
    db.commit()
    db.refresh(job)
    return job
