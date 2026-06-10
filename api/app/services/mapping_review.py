"""Mapping review — confirm corrected mappings and resume analysis."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import IngestJob, Organization, Organization
from app.services.analysis import run_operational_analysis
from app.services.etl.field_mapper import FieldMapping, MappingPlan, _REQUIRED_FIELDS
from app.services.etl.interpretation import interpret_upload
from app.services.mapping_memory import save_org_mapping_memory
from app.services.storage import read_upload_to_dataframe
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
            reason=val.get("reason", ""),
        )
    return MappingPlan(
        report_type=job.report_type or meta.get("report_type") or "unknown",
        field_mapping=field_mapping,
        amount_strategy=meta.get("amount_strategy", "single_column"),
        bucket_columns=meta.get("bucket_columns") or [],
        unmapped_columns=meta.get("unmapped_columns") or [],
        overall_confidence=float(job.mapping_confidence or 0),
        parse_warnings=meta.get("parse_warnings") or [],
        column_map=meta.get("column_map") or {},
    )


def get_mapping_review(db: Session, job: IngestJob) -> dict:
    org = db.get(Organization, job.org_id)
    intake = read_upload_to_dataframe(job.storage_key, job.file_name)
    meta = job.mapping_metadata or {}
    mapping_answers = meta.get("mapping_answers") or {}

    interpretation = interpret_upload(
        intake.dataframe,
        job.file_name,
        org=org,
        mapping_answers=mapping_answers,
    )

    plan = _plan_from_job(job)
    if plan.column_map:
        interpretation.mapping_plan.column_map.update(plan.column_map)
        interpretation.mapping_plan.field_mapping.update(plan.field_mapping)

    report_type = job.report_type or interpretation.classification.likely_type
    canonical_fields = sorted(
        set(_REQUIRED_FIELDS.get(report_type, []))
        | set(_REQUIRED_FIELDS.get(interpretation.mapping_plan.report_type, []))
        | set(interpretation.mapping_plan.field_mapping.keys())
    )

    return {
        "job_id": str(job.id),
        "status": job.status,
        "mapping_status": job.mapping_status,
        "report_type": report_type,
        "mapping_confidence": job.mapping_confidence,
        "classification": meta.get("classification") or interpretation.classification.to_dict(),
        "row_meaning": meta.get("row_meaning") or interpretation.row_meaning.to_dict(),
        "analysis_readiness": meta.get("analysis_readiness")
        or (interpretation.readiness.to_dict() if interpretation.readiness else None),
        "data_profile": meta.get("data_profile") or interpretation.data_profile.to_dict(),
        "column_mappings": meta.get("column_mappings")
        or [cm.to_dict() for cm in interpretation.column_mappings],
        "missing_fields": meta.get("missing_fields") or interpretation.missing_fields,
        "questions": meta.get("questions") or [q.to_dict() for q in interpretation.questions],
        "schema_memory": meta.get("schema_memory")
        or (interpretation.schema_memory.to_dict() if interpretation.schema_memory else {"match": "none"}),
        "mapping": interpretation.mapping_plan.to_dict(),
        "intake_metadata": job.intake_metadata or intake.metadata.to_dict(),
        "sample_rows": interpretation.data_profile.sample_rows,
        "columns": list(intake.dataframe.columns),
        "canonical_fields": canonical_fields,
        "unmapped_columns": interpretation.mapping_plan.unmapped_columns,
        "mapping_answers": mapping_answers,
    }


def confirm_job_mapping(
    db: Session,
    org: Organization,
    job: IngestJob,
    column_map: dict[str, str] | None = None,
    amount_strategy: str | None = None,
    mapping_answers: dict[str, str] | None = None,
    row_meaning: str | None = None,
    apply_schema_memory: bool | None = None,
) -> IngestJob:
    if job.status not in ("needs_review", "processing"):
        raise ValueError(f"Job cannot be confirmed from status: {job.status}")

    intake = read_upload_to_dataframe(job.storage_key, job.file_name)
    meta = job.mapping_metadata or {}
    prior_answers = dict(meta.get("mapping_answers") or {})
    if mapping_answers:
        prior_answers.update(mapping_answers)
    if row_meaning:
        prior_answers["row_meaning"] = row_meaning

    interpretation = interpret_upload(
        intake.dataframe,
        job.file_name,
        org=org,
        mapping_answers=prior_answers,
        user_confirmed=True,
    )
    plan = interpretation.mapping_plan

    if apply_schema_memory and interpretation.schema_memory and interpretation.schema_memory.prior_mapping:
        prior = interpretation.schema_memory.prior_mapping
        if prior.get("column_map"):
            plan.column_map.update(prior["column_map"])
        if prior.get("amount_strategy"):
            plan.amount_strategy = prior["amount_strategy"]

    if column_map:
        plan.column_map.update(column_map)
        for orig, canonical in column_map.items():
            if orig and canonical:
                plan.field_mapping[canonical] = FieldMapping(
                    source=orig, confidence=1.0, strategy="single_column"
                )

    if amount_strategy:
        plan.amount_strategy = amount_strategy
        prior_answers["gl_amount_semantics"] = amount_strategy
    elif prior_answers.get("gl_amount_semantics"):
        plan.amount_strategy = prior_answers["gl_amount_semantics"]

    readiness = interpretation.readiness
    if readiness and not readiness.ready:
        unanswered = [q for q in interpretation.questions if q.required_before_analysis and not prior_answers.get(q.id)]
        if unanswered:
            raise ValueError(
                f"Required questions unanswered: {', '.join(q.id for q in unanswered)}"
            )

    report_type = job.report_type or interpretation.classification.likely_type
    if report_type == "unknown_operational_export":
        report_type = plan.report_type or "unknown"

    period = job.detected_period or "unknown"
    adapter = jobboss_adapter if org.erp_family == "jobboss" else generic_adapter
    dataset = adapter.dataframe_to_canonical(report_type, intake.dataframe, plan=plan)
    row_count = persist_canonical(db, org.id, job.id, period, dataset)

    job.mapping_status = "user_confirmed"
    job.report_type = report_type
    prior_meta = job.mapping_metadata or {}
    job.mapping_metadata = {
        **interpretation.to_metadata(),
        **plan.to_dict(),
        "mapping_answers": prior_answers,
        "row_meaning": interpretation.row_meaning.to_dict(),
        "extra_column_samples": prior_meta.get("extra_column_samples") or {},
        "coverage_score": dataset.coverage_score,
        "normalized_rows": dataset.normalized_rows,
        "rejected_rows": [r.model_dump() for r in dataset.rejected_rows],
    }
    if interpretation.readiness:
        updated_readiness = interpretation.readiness
        updated_readiness.ready = True
        updated_readiness.score = max(updated_readiness.score, 0.85)
        job.mapping_metadata["analysis_readiness"] = updated_readiness.to_dict()

    job.mapping_confidence = interpretation.classification.confidence
    job.row_count = row_count
    job.status = "processing"
    save_org_mapping_memory(
        org,
        plan,
        list(intake.dataframe.columns),
        mapping_answers=prior_answers,
        row_meaning=prior_answers.get("row_meaning") or row_meaning,
    )
    db.flush()

    analysis = run_operational_analysis(db, org.id, job.id, period=period)
    job.report_id = analysis.report.id
    job.status = "done"
    db.commit()
    db.refresh(job)
    return job
