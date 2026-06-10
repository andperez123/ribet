from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models import IngestJob, OperationalFinding, OperationalMemory, OperationalReport, Organization
from app.services.digest import (
    build_data_coverage,
    build_data_digest,
    build_domain_insights,
    build_executive_summary,
    domains_for_report_type,
)
from app.services.events import emit_event
from app.services.health import build_trend_snapshot, compute_health, get_prior_snapshot
from app.services.ai_analyst.runner import (
    AnalystResult,
    persist_report_narrative,
    run_ai_analyst,
)
from app.services.evidence_pack import build_evidence_pack, persist_evidence_pack
from app.services.agent_contract import finalize_report_contract
from app.services.pipeline_stage import set_job_pipeline_stage
from app.services.report_contract import build_report_contract, get_covered_domains
from app.services.report_insights import validate_insights_invariant
from app.services.analysis_context import AnalysisContext
from app.services.graph.coverage import get_graph_coverage
from app.services.rules.cross_sector import run_cross_sector_rules
from app.services.rules.runner import run_rules, run_snapshot_delta_rules
from app.services.rules.types import RuleFinding
from app.services.telemetry import track_stage
from app.services.improvements import build_improvement_notes
from app.services.series import append_series_snapshot, get_or_create_series, get_prior_series_snapshot
from app.services.memory import upsert_memory
from app.services.transforms.snapshot import (
    build_operational_snapshot,
    get_prior_snapshot as get_prior_op_snapshot,
    snapshot_delta_strings,
)


def persist_findings(
    db: Session,
    org_id: UUID,
    job_id: UUID,
    report_id: UUID,
    findings: list[RuleFinding],
    narratives: dict[str, dict[str, str]] | None = None,
) -> None:
    narratives = narratives or {}
    for f in findings:
        extra = narratives.get(f.fingerprint, {})
        db.add(
            OperationalFinding(
                org_id=org_id,
                job_id=job_id,
                report_id=report_id,
                finding_type=f.finding_type,
                title=f.title,
                detail=f.detail,
                severity=f.severity,
                confidence=f.confidence,
                business_impact=f.business_impact,
                department=f.department,
                category=f.category,
                fingerprint=f.fingerprint,
                finding_id=f.finding_id or None,
                finding_instance_id=f.finding_instance_id or None,
                suggested_action=extra.get("recommendation") or f.suggested_action,
                narrative=extra.get("narrative"),
                recommendation=extra.get("recommendation"),
            )
        )


def _merge_narratives_into_dicts(
    finding_dicts: list[dict],
    narratives: dict[str, dict[str, str]],
) -> list[dict]:
    merged: list[dict] = []
    for d in finding_dicts:
        row = dict(d)
        extra = narratives.get(row.get("fingerprint", ""), {})
        if extra.get("narrative"):
            row["narrative"] = extra["narrative"]
        if extra.get("recommendation"):
            row["recommendation"] = extra["recommendation"]
            row["suggested_action"] = extra["recommendation"]
        merged.append(row)
    return merged


def _analysis_metadata_from_analyst(
    result: AnalystResult,
    finding_count: int,
    coverage: dict[str, bool],
) -> dict:
    domains = [k for k, v in coverage.items() if v and k in ("ar", "ap", "gl", "inventory")]
    if result.skipped:
        status = "skipped"
    elif result.used_fallback:
        status = "fallback"
    elif result.output:
        status = "completed"
    else:
        status = "failed"
    meta = {
        "narration": status,
        "model": result.model_name,
        "finding_count": finding_count,
        "narrated_count": len(result.output.top_risks) if result.output else 0,
        "data_domains_present": domains,
        "duration_ms": result.duration_ms or None,
        "ai_analyst": True,
        "verification_status": result.verification_status,
        "used_fallback": result.used_fallback,
    }
    if result.output:
        meta["executive_bullets"] = len(result.output.executive_summary)
        meta["top_risks_count"] = len(result.output.top_risks)
    return meta


def _narratives_from_analyst_output(result: AnalystResult, findings: list[RuleFinding]) -> dict[str, dict[str, str]]:
    narratives: dict[str, dict[str, str]] = {}
    if not result.output:
        return narratives

    id_to_finding = {f.finding_id: f for f in findings if f.finding_id}
    for risk in result.output.top_risks:
        for fid in risk.finding_ids:
            finding = id_to_finding.get(fid)
            if finding:
                narratives[finding.fingerprint] = {
                    "narrative": risk.narrative,
                    "recommendation": risk.recommended_action,
                }

    if result.output.executive_summary:
        narratives["__executive__"] = {
            "narrative": " ".join(result.output.executive_summary),
            "recommendation": "",
        }
    return narratives


def _management_questions_from_analyst(result: AnalystResult) -> list[str]:
    if not result.output:
        return []
    return [q.question for q in result.output.management_questions if q.question.strip()]


def generate_report(
    db: Session,
    org_id: UUID,
    job_ids: list[UUID],
    period: str | None = None,
) -> OperationalReport:
    job_id = job_ids[0] if job_ids else None
    period_label = period or datetime.now(timezone.utc).strftime("%Y-%m")
    trigger_job = db.get(IngestJob, job_id) if job_id else None
    trigger_domains = domains_for_report_type(trigger_job.report_type if trigger_job else None)
    covered_domains = get_covered_domains(db, org_id)
    primary_domain = None
    if trigger_job and trigger_job.report_type:
        primary_domain = {
            "ar_aging": "ar",
            "ap_aging": "ap",
            "gl_detail": "gl",
            "gl_trial_balance": "gl",
            "inventory": "inventory",
            "purchase_orders": "orders",
            "sales_orders": "sales",
        }.get(trigger_job.report_type)

    with track_stage(db, "rules", org_id=org_id, job_id=job_id):
        ctx = AnalysisContext(
            org_id=org_id,
            period=period_label,
            source_job_ids=job_ids or None,
            domains=trigger_domains or set(),
        )
        ctx.prior_op_snap = get_prior_op_snapshot(db, org_id, exclude_period=period_label)
        findings = run_rules(
            db,
            org_id,
            period=period_label,
            source_job_ids=job_ids or None,
            domains=trigger_domains,
        )

    org = db.get(Organization, org_id)
    org_name = org.name if org else "Organization"

    report = OperationalReport(org_id=org_id, job_ids=[str(j) for j in job_ids], period_label=period_label)
    db.add(report)
    db.flush()

    op_snap = build_operational_snapshot(
        db,
        org_id,
        period_label,
        job_ids[0] if job_ids else org_id,
        100,
        "Stable",
    )
    ctx.op_snap = op_snap
    ctx.coverage = get_graph_coverage(db, org_id)
    ctx.findings = findings

    with track_stage(db, "rules_cross_sector", org_id=org_id, job_id=job_id):
        cross_domain_findings = run_cross_sector_rules(db, ctx)
        findings.extend(cross_domain_findings)
        ctx.findings = findings

    health_snap = compute_health(db, org_id, findings, report.id)
    op_snap.health_score = health_snap.score
    op_snap.health_status = health_snap.status
    db.flush()

    ctx.op_snap = op_snap
    with track_stage(db, "rules_delta", org_id=org_id, job_id=job_id):
        findings.extend(run_snapshot_delta_rules(db, ctx))

    upsert_memory(db, org_id, findings)

    prior_op = ctx.prior_op_snap
    prior_health = get_prior_snapshot(db, org_id, exclude_id=health_snap.id)
    trends = build_trend_snapshot(health_snap, prior_health, findings)
    trends = list(trends) + snapshot_delta_strings(op_snap, prior_op)

    primary_digest = build_data_digest(
        db,
        org_id,
        period=period_label,
        source_job_ids=job_ids or None,
        domains=trigger_domains,
    )
    org_digest = None
    org_insights_raw: list = []
    if covered_domains and (
        not trigger_domains or covered_domains != trigger_domains
    ):
        org_digest = build_data_digest(
            db,
            org_id,
            period=period_label,
            domains=covered_domains,
        )
        org_insights_raw = build_domain_insights(org_digest, findings)

    coverage = build_data_coverage(primary_digest, primary_domain=primary_domain)
    domain_insights_objs = build_domain_insights(primary_digest, findings)
    domain_insights = [i.to_dict() for i in domain_insights_objs]

    validate_insights_invariant(primary_digest.to_dict(), domain_insights)

    executive = build_executive_summary(primary_digest, findings)
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    seen_actions: set[str] = set()
    actions: list[str] = []
    for f in sorted(findings, key=lambda x: severity_rank.get(x.severity, 0), reverse=True):
        act = f.suggested_action
        if act and act not in seen_actions:
            seen_actions.add(act)
            actions.append(act)

    analyst_result = AnalystResult(skipped=True)
    narratives: dict[str, dict[str, str]] = {}
    analyst_summary: str | None = None
    management_questions: list[str] = []

    financial = [f.to_dict() for f in findings if f.category == "financial"]
    operational = [f.to_dict() for f in findings if f.category == "operational"]
    risk = [
        f.to_dict()
        for f in findings
        if f.severity in ("high", "critical") or f.category == "risk"
    ]

    report.executive_summary = executive
    report.financial_findings = financial
    report.operational_findings = operational
    report.risk_areas = risk
    report.suggested_actions = actions
    report.trend_snapshot = trends
    report.health_score = health_snap.score
    report.health_status = health_snap.status
    report.data_digest = primary_digest.to_dict()
    report.domain_insights = domain_insights
    report.data_coverage = coverage

    report.report_contract = build_report_contract(
        db,
        org_id,
        report.id,
        trigger_job,
        job_ids,
        period_label,
        trigger_domains,
        primary_digest,
        domain_insights_objs,
        findings,
        executive,
        covered_domains,
        org_digest,
        org_insights_raw,
        cross_domain_findings,
    )
    report.domain_insights = report.report_contract.get("domain_insights", domain_insights)

    if job_ids:
        with track_stage(
            db,
            "report_persist",
            org_id=org_id,
            job_id=job_id,
            report_id=report.id,
            extra={"finding_count": len(findings)},
        ):
            persist_findings(db, org_id, job_ids[0], report.id, findings, narratives)
            db.flush()

    with track_stage(db, "evidence_pack", org_id=org_id, job_id=job_id, report_id=report.id):
        trigger_job_ref = db.get(IngestJob, job_id) if job_id else None
        set_job_pipeline_stage(db, trigger_job_ref, "evidence_pack")
        pack = build_evidence_pack(db, report.id, findings=findings)
        persist_evidence_pack(db, report.id, pack)

    if settings.ribet_narration.lower() == "on" and settings.openai_api_key:
        emit_event(
            db,
            "ai_analyst_started",
            org_id=org_id,
            job_id=job_id,
            report_id=report.id,
            metadata={"finding_count": len(findings)},
        )
        db.commit()

    with track_stage(db, "ai_analyst", org_id=org_id, job_id=job_id, report_id=report.id):
        set_job_pipeline_stage(db, trigger_job_ref, "ai_analyst")
        analyst_result = run_ai_analyst(pack)
        set_job_pipeline_stage(db, trigger_job_ref, "verification")
        persist_report_narrative(db, report.id, org_id, analyst_result)

    if analyst_result.skipped:
        pass
    elif analyst_result.used_fallback or analyst_result.verification_status == "fallback":
        emit_event(
            db,
            "ai_analyst_fallback",
            org_id=org_id,
            job_id=job_id,
            report_id=report.id,
            metadata={"failures": analyst_result.verification_failures},
        )
    elif analyst_result.output:
        emit_event(
            db,
            "ai_analyst_completed",
            org_id=org_id,
            job_id=job_id,
            report_id=report.id,
            metadata={"duration_ms": analyst_result.duration_ms},
        )

    narratives = _narratives_from_analyst_output(analyst_result, findings)
    management_questions = _management_questions_from_analyst(analyst_result)
    if analyst_result.output and analyst_result.output.executive_summary:
        analyst_summary = " ".join(analyst_result.output.executive_summary)

    recurring = (
        db.query(OperationalMemory)
        .filter(OperationalMemory.org_id == org_id, OperationalMemory.occurrence_count > 1)
        .all()
    )
    risk = _merge_narratives_into_dicts(risk, narratives)
    for mem in recurring:
        risk.append(
            {
                "title": mem.title,
                "detail": f"Detected {mem.occurrence_count} times. Last seen {mem.last_seen_at.isoformat()}.",
                "severity": mem.severity_peak,
                "category": "risk",
                "finding_type": mem.finding_type,
            }
        )
    report.financial_findings = _merge_narratives_into_dicts(financial, narratives)
    report.operational_findings = _merge_narratives_into_dicts(operational, narratives)
    report.risk_areas = risk
    report.analyst_summary = analyst_summary
    report.management_questions = management_questions
    report.analysis_metadata = _analysis_metadata_from_analyst(analyst_result, len(findings), coverage)

    report.report_contract = finalize_report_contract(
        report.report_contract or {},
        db,
        org_id,
        findings,
        coverage,
        primary_digest,
        pack,
        analyst_result,
        trigger_job,
        period_label,
    )

    if job_id:
        job = db.get(IngestJob, job_id)
        if job and job.schema_fingerprint and job.report_type:
            series = get_or_create_series(
                db, org_id, job.report_type, job.schema_fingerprint, job
            )
            prior_snap = get_prior_series_snapshot(db, series.id)
            kpi_summary = {
                "ar_total": primary_digest.ar_total,
                "ar_over_90_pct": primary_digest.ar_over_90_pct,
                "ap_total": primary_digest.ap_total,
                "health_score": health_snap.score,
                "health_status": health_snap.status,
                "vendor_concentration": op_snap.vendor_concentration,
            }
            improvement_notes = build_improvement_notes(kpi_summary, prior_snap)
            report.improvement_notes = improvement_notes
            append_series_snapshot(
                db,
                org_id=org_id,
                series=series,
                period=period_label,
                job_id=job_id,
                report_id=report.id,
                content_hash=job.content_hash,
                kpi_summary=kpi_summary,
                improvement_notes=improvement_notes,
            )

    db.commit()
    db.refresh(report)
    emit_event(
        db,
        "report_generated",
        org_id=org_id,
        report_id=report.id,
        job_id=job_id,
        metadata={
            "health_score": report.health_score,
            "finding_count": len(findings),
            "narration_failed": analyst_result.verification_status == "failed",
            "ai_analyst_fallback": analyst_result.used_fallback,
            "narration_ms": analyst_result.duration_ms,
            "data_domains": [k for k, v in coverage.items() if v],
        },
    )
    db.commit()
    return report


def delete_report(db: Session, org_id: UUID, report_id: UUID) -> bool:
    """Delete a report and its dependent rows. Returns False if not found."""
    from sqlalchemy import delete, update

    from app.models import (
        EvidencePackRecord,
        HealthSnapshot,
        IngestJob,
        OperationalFinding,
        ProductEvent,
        ReportNarrative,
        SeriesSnapshot,
    )

    report = db.get(OperationalReport, report_id)
    if not report or report.org_id != org_id:
        return False

    db.execute(
        delete(OperationalFinding).where(OperationalFinding.report_id == report_id)
    )
    db.execute(delete(EvidencePackRecord).where(EvidencePackRecord.report_id == report_id))
    db.execute(delete(ReportNarrative).where(ReportNarrative.report_id == report_id))
    db.execute(delete(HealthSnapshot).where(HealthSnapshot.report_id == report_id))
    db.execute(delete(ProductEvent).where(ProductEvent.report_id == report_id))
    db.execute(delete(SeriesSnapshot).where(SeriesSnapshot.report_id == report_id))
    db.execute(
        update(IngestJob)
        .where(IngestJob.report_id == report_id)
        .values(report_id=None)
    )
    db.delete(report)
    db.commit()
    return True
