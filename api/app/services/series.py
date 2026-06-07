"""Data series matching and immutable snapshot history."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import DataSeries, IngestJob, SeriesSnapshot


def _display_name(job: IngestJob | None, report_type: str) -> str:
    if job and job.user_description:
        return job.user_description[:256]
    labels = {
        "ar_aging": "AR Aging",
        "ap_aging": "AP Aging",
        "gl_detail": "GL Detail",
        "inventory": "Inventory",
    }
    return labels.get(report_type, report_type.replace("_", " ").title())


def get_or_create_series(
    db: Session,
    org_id: UUID,
    report_type: str,
    schema_fingerprint: str,
    job: IngestJob | None = None,
) -> DataSeries:
    existing = (
        db.query(DataSeries)
        .filter(
            DataSeries.org_id == org_id,
            DataSeries.schema_fingerprint == schema_fingerprint,
            DataSeries.report_type == report_type,
        )
        .first()
    )
    if existing:
        return existing
    series = DataSeries(
        org_id=org_id,
        report_type=report_type,
        schema_fingerprint=schema_fingerprint,
        display_name=_display_name(job, report_type),
    )
    db.add(series)
    db.flush()
    return series


def get_prior_series_snapshot(db: Session, series_id: UUID) -> SeriesSnapshot | None:
    return (
        db.query(SeriesSnapshot)
        .filter(SeriesSnapshot.series_id == series_id)
        .order_by(SeriesSnapshot.snapshot_at.desc())
        .first()
    )


def append_series_snapshot(
    db: Session,
    *,
    org_id: UUID,
    series: DataSeries,
    period: str,
    job_id: UUID,
    report_id: UUID,
    content_hash: str | None,
    kpi_summary: dict,
    improvement_notes: list[dict],
) -> SeriesSnapshot:
    snap = SeriesSnapshot(
        series_id=series.id,
        org_id=org_id,
        period=period,
        job_id=job_id,
        report_id=report_id,
        content_hash=content_hash,
        kpi_summary=kpi_summary,
        improvement_notes=improvement_notes,
    )
    db.add(snap)
    db.flush()
    return snap
