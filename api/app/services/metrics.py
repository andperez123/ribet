from datetime import datetime, timedelta, timezone
from statistics import median

from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from app.models import (
    HealthSnapshot,
    IngestJob,
    OperationalFinding,
    OperationalReport,
    Organization,
    OrgProgress,
)
from app.schemas.metrics import (
    ActivationBlock,
    AdminMetricsOut,
    EngagementBlock,
    OrgMetricsRow,
    TotalsBlock,
    WeeklyBucket,
)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()


def compute_admin_metrics(db: Session, weeks: int = 12) -> AdminMetricsOut:
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    week_start = now - timedelta(weeks=weeks)

    total_orgs = db.query(func.count(Organization.id)).scalar() or 0
    total_uploads = db.query(func.count(IngestJob.id)).scalar() or 0
    total_reports = db.query(func.count(OperationalReport.id)).scalar() or 0
    total_findings = db.query(func.count(OperationalFinding.id)).scalar() or 0
    active_orgs_30d = (
        db.query(func.count(distinct(IngestJob.org_id)))
        .filter(IngestJob.created_at >= thirty_days_ago)
        .scalar()
        or 0
    )

    orgs_with_report = (
        db.query(func.count(distinct(OperationalReport.org_id))).scalar() or 0
    )
    activation_rate = (orgs_with_report / total_orgs * 100) if total_orgs > 0 else 0.0

    first_report_subq = (
        db.query(
            OperationalReport.org_id,
            func.min(OperationalReport.generated_at).label("first_at"),
        )
        .group_by(OperationalReport.org_id)
        .subquery()
    )
    ttf_rows = (
        db.query(Organization.created_at, first_report_subq.c.first_at)
        .join(first_report_subq, Organization.id == first_report_subq.c.org_id)
        .all()
    )
    ttf_hours = [
        (first_at - org_created).total_seconds() / 3600
        for org_created, first_at in ttf_rows
        if org_created and first_at
    ]
    median_ttf = median(ttf_hours) if ttf_hours else None

    done_jobs = (
        db.query(func.count(IngestJob.id)).filter(IngestJob.status == "done").scalar() or 0
    )
    upload_success_rate = (done_jobs / total_uploads * 100) if total_uploads > 0 else 0.0

    jobs_with_report = (
        db.query(func.count(IngestJob.id))
        .filter(IngestJob.status == "done", IngestJob.report_id.isnot(None))
        .scalar()
        or 0
    )
    report_yield_rate = (jobs_with_report / done_jobs * 100) if done_jobs > 0 else 0.0

    progress_rows = db.query(OrgProgress).all()
    sector_counts: list[int] = []
    for progress in progress_rows:
        covered = progress.sectors_covered or {}
        sector_counts.append(sum(1 for s in covered.values() if (s or {}).get("count", 0) > 0))
    avg_sectors = sum(sector_counts) / len(sector_counts) if sector_counts else 0.0

    upload_counts = (
        db.query(IngestJob.org_id, func.count(IngestJob.id).label("cnt"))
        .group_by(IngestJob.org_id)
        .all()
    )
    orgs_with_uploads = [row for row in upload_counts if row.cnt > 0]
    repeat_orgs = sum(1 for row in upload_counts if row.cnt > 1)
    repeat_rate = (
        (repeat_orgs / len(orgs_with_uploads) * 100) if orgs_with_uploads else 0.0
    )

    avg_findings = (total_findings / total_reports) if total_reports > 0 else 0.0

    weekly = _weekly_buckets(db, week_start, weeks, now)

    org_rows = _org_metrics_rows(db)

    return AdminMetricsOut(
        generated_at=now.isoformat(),
        totals=TotalsBlock(
            orgs=total_orgs,
            uploads=total_uploads,
            reports=total_reports,
            findings=total_findings,
            active_orgs_30d=active_orgs_30d,
        ),
        activation=ActivationBlock(
            rate_pct=round(activation_rate, 1),
            orgs_with_report=orgs_with_report,
            median_time_to_first_report_hours=round(median_ttf, 1) if median_ttf is not None else None,
        ),
        engagement=EngagementBlock(
            upload_success_rate_pct=round(upload_success_rate, 1),
            report_yield_rate_pct=round(report_yield_rate, 1),
            avg_sectors_per_active_org=round(avg_sectors, 1),
            repeat_upload_rate_pct=round(repeat_rate, 1),
            avg_findings_per_report=round(avg_findings, 1),
        ),
        weekly=weekly,
        orgs=org_rows,
    )


def _week_start(dt: datetime) -> datetime:
    d = dt.astimezone(timezone.utc)
    return (d - timedelta(days=d.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def _weekly_buckets(
    db: Session, since: datetime, weeks: int, now: datetime
) -> list[WeeklyBucket]:
    buckets: dict[datetime, WeeklyBucket] = {}
    current = _week_start(since)
    end = _week_start(now)
    while current <= end:
        buckets[current] = WeeklyBucket(
            week_start=current.date().isoformat(),
            uploads=0,
            reports=0,
            new_orgs=0,
            cumulative_reports=0,
        )
        current += timedelta(weeks=1)

    for job in db.query(IngestJob.created_at).filter(IngestJob.created_at >= since).all():
        if job.created_at:
            key = _week_start(job.created_at)
            if key in buckets:
                buckets[key].uploads += 1

    for report in (
        db.query(OperationalReport.generated_at)
        .filter(OperationalReport.generated_at >= since)
        .all()
    ):
        if report.generated_at:
            key = _week_start(report.generated_at)
            if key in buckets:
                buckets[key].reports += 1

    for org in db.query(Organization.created_at).filter(Organization.created_at >= since).all():
        if org.created_at:
            key = _week_start(org.created_at)
            if key in buckets:
                buckets[key].new_orgs += 1

    reports_before = (
        db.query(func.count(OperationalReport.id))
        .filter(OperationalReport.generated_at < since)
        .scalar()
        or 0
    )
    cumulative = reports_before
    result: list[WeeklyBucket] = []
    for key in sorted(buckets.keys()):
        bucket = buckets[key]
        cumulative += bucket.reports
        bucket.cumulative_reports = cumulative
        result.append(bucket)
    return result


def _org_metrics_rows(db: Session) -> list[OrgMetricsRow]:
    orgs = db.query(Organization).order_by(Organization.created_at.desc()).all()
    rows: list[OrgMetricsRow] = []

    for org in orgs:
        uploads = (
            db.query(func.count(IngestJob.id)).filter(IngestJob.org_id == org.id).scalar() or 0
        )
        reports = (
            db.query(func.count(OperationalReport.id))
            .filter(OperationalReport.org_id == org.id)
            .scalar()
            or 0
        )
        findings = (
            db.query(func.count(OperationalFinding.id))
            .filter(OperationalFinding.org_id == org.id)
            .scalar()
            or 0
        )

        last_upload = (
            db.query(func.max(IngestJob.created_at))
            .filter(IngestJob.org_id == org.id)
            .scalar()
        )
        last_report = (
            db.query(func.max(OperationalReport.generated_at))
            .filter(OperationalReport.org_id == org.id)
            .scalar()
        )

        progress = db.get(OrgProgress, org.id)
        sectors_covered = 0
        if progress and progress.sectors_covered:
            sectors_covered = sum(
                1 for s in progress.sectors_covered.values() if (s or {}).get("count", 0) > 0
            )

        latest_health = (
            db.query(HealthSnapshot)
            .filter(HealthSnapshot.org_id == org.id)
            .order_by(HealthSnapshot.computed_at.desc())
            .first()
        )

        rows.append(
            OrgMetricsRow(
                org_id=str(org.id),
                name=org.name,
                created_at=_iso(org.created_at) or "",
                uploads=uploads,
                reports=reports,
                sectors_covered=sectors_covered,
                findings=findings,
                last_upload_at=_iso(last_upload),
                last_report_at=_iso(last_report),
                health_score=latest_health.score if latest_health else None,
            )
        )

    return rows
