from __future__ import annotations

"""Report Generation Contract — stable UI-ready payload for every report."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import IngestJob, OperationalReport
from app.services.digest import (
    DataDigest,
    DomainInsight,
    sort_domain_insights,
)
from app.services.gaps import _gap_specs, get_open_gaps
from app.services.graph.confidence import CONFIDENCE_WEIGHTS, compute_analysis_confidence
from app.services.graph.coverage import COVERAGE_SPECS, get_graph_coverage
from app.services.rules.runner import RuleFinding

REPORT_TYPE_LABELS: dict[str, str] = {
    "ar_aging": "AR Aging",
    "ap_aging": "AP Aging",
    "gl_detail": "GL Detail",
    "inventory": "Inventory",
    "purchase_orders": "Purchase Orders",
    "sales_orders": "Open Sales Orders",
}

DOMAIN_TO_REPORT_TYPE: dict[str, str] = {
    "ar": "ar_aging",
    "ap": "ap_aging",
    "gl": "gl_detail",
    "inventory": "inventory",
    "orders": "purchase_orders",
    "sales": "sales_orders",
}

FINDING_GAP_TYPES: dict[str, str] = {
    "ar_aging_spike": "missing_invoice_detail",
    "vendor_concentration": "missing_purchase_orders",
    "vendor_name_concentration": "missing_purchase_orders",
    "inventory_adjustment_spike": "missing_work_orders",
    "orphan_inventory": "missing_work_orders",
    "operational_cash_pressure": "cash_pressure_diagnosis",
}

CROSS_DOMAIN_FINDING_TYPES = {
    "operational_cash_pressure",
    "ar_ap_working_capital",
    "gl_inventory_writeoff_pattern",
    "po_so_fulfillment_gap",
}


def get_covered_domains(db: Session, org_id: UUID) -> set[str]:
    coverage = get_graph_coverage(db, org_id)
    domains: set[str] = set()
    for spec in COVERAGE_SPECS:
        if spec["uploadable"] and coverage.has(spec["key"]):
            rt = spec["report_type"]
            domain = {
                "ar_aging": "ar",
                "ap_aging": "ap",
                "gl_detail": "gl",
                "inventory": "inventory",
                "purchase_orders": "orders",
                "sales_orders": "sales",
            }.get(rt)
            if domain:
                domains.add(domain)
    return domains


def _row_count_for_job(job: IngestJob | None) -> int:
    if job and job.row_count is not None:
        return int(job.row_count)
    return 0


def build_source_traceability(
    trigger_job: IngestJob | None,
    period: str,
    row_count: int | None = None,
) -> dict:
    report_type = trigger_job.report_type if trigger_job else None
    upload_label = REPORT_TYPE_LABELS.get(report_type or "", "Upload")
    rows = row_count if row_count is not None else _row_count_for_job(trigger_job)
    return {
        "upload_label": upload_label,
        "period": period,
        "row_count": rows,
        "job_id": str(trigger_job.id) if trigger_job else None,
        "report_type": report_type,
        "source_label": f"Based on: {upload_label} upload · {period} · {rows} rows analyzed",
    }


def _attach_source_to_insights(
    insights: list[dict],
    trace: dict,
) -> list[dict]:
    label = trace.get("source_label", "")
    out: list[dict] = []
    for item in insights:
        row = dict(item)
        row["source_label"] = label
        out.append(row)
    return out


def _gap_recommendation_for_finding(
    finding_type: str,
    gap_specs: list,
) -> str | None:
    gap_type = FINDING_GAP_TYPES.get(finding_type)
    if not gap_type:
        return None
    for spec in gap_specs:
        if spec.gap_type == gap_type:
            uploads = ", ".join(spec.recommended_uploads)
            return f"Upload {uploads} to investigate further: {spec.reason}"
    return None


def build_top_signals(
    findings: list[RuleFinding],
    insights: list[dict],
    executive_summary: list[str],
    limit: int = 5,
) -> list[dict]:
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    insight_rank = {"alert": 0, "watch": 1, "info": 2}
    signals: list[dict] = []

    for f in sorted(findings, key=lambda x: severity_rank.get(x.severity, 9)):
        if len(signals) >= limit:
            break
        if f.finding_type in CROSS_DOMAIN_FINDING_TYPES and len(signals) >= 3:
            continue
        signals.append(
            {
                "kind": "finding",
                "title": f.title,
                "body": f.detail,
                "why_it_matters": f.business_impact or f.detail,
                "severity": f.severity,
                "suggested_action": f.suggested_action or None,
                "finding_id": f.finding_id or None,
            }
        )

    for insight in sorted(insights, key=lambda x: insight_rank.get(x.get("severity", "info"), 9)):
        if len(signals) >= limit:
            break
        if insight.get("severity") == "info" and len(signals) >= 3:
            continue
        signals.append(
            {
                "kind": "insight",
                "title": insight.get("title", ""),
                "body": insight.get("body", ""),
                "severity": insight.get("severity", "info"),
                "metric_label": insight.get("metric_label"),
                "metric_value": insight.get("metric_value"),
                "source": insight.get("source_label"),
            }
        )

    for line in executive_summary:
        if len(signals) >= limit:
            break
        if any(s.get("body") == line for s in signals):
            continue
        signals.append(
            {
                "kind": "executive",
                "title": "Executive summary",
                "body": line,
                "severity": "medium",
            }
        )

    return signals[:limit]


def build_action_items(
    findings: list[RuleFinding],
    gap_specs: list,
    limit: int = 10,
) -> list[dict]:
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    items: list[dict] = []
    for f in sorted(findings, key=lambda x: severity_rank.get(x.severity, 0), reverse=True):
        if len(items) >= limit:
            break
        items.append(
            {
                "title": f.title,
                "detail": f.detail,
                "severity": f.severity,
                "suggested_action": f.suggested_action or None,
                "gap_recommendation": _gap_recommendation_for_finding(f.finding_type, gap_specs),
                "finding_type": f.finding_type,
            }
        )
    return items


def compute_confidence_delta(
    db: Session,
    org_id: UUID,
    trigger_job: IngestJob | None,
) -> dict:
    coverage = get_graph_coverage(db, org_id)
    confidence_after = compute_analysis_confidence(coverage).score
    confidence_before = confidence_after

    if trigger_job and trigger_job.report_type:
        prior_same_type = (
            db.query(IngestJob)
            .filter(
                IngestJob.org_id == org_id,
                IngestJob.status == "done",
                IngestJob.report_type == trigger_job.report_type,
                IngestJob.id != trigger_job.id,
            )
            .count()
        )
        if prior_same_type == 0:
            weight = CONFIDENCE_WEIGHTS.get(trigger_job.report_type, 0)
            confidence_before = max(0, confidence_after - weight)

    return {
        "before": confidence_before,
        "after": confidence_after,
        "delta": confidence_after - confidence_before,
    }


def build_coverage_delta(
    trigger_job: IngestJob | None,
    confidence: dict,
) -> dict | None:
    if not trigger_job or not trigger_job.report_type:
        return None
    label = REPORT_TYPE_LABELS.get(trigger_job.report_type, trigger_job.report_type)
    delta = confidence.get("delta", 0)
    if delta <= 0:
        return {
            "upload_label": label,
            "message": f"You uploaded {label}. Ribet refreshed analysis for this data.",
        }
    return {
        "upload_label": label,
        "message": (
            f"You uploaded {label}. Ribet can now incorporate this into your operational picture. "
            f"Analysis confidence: {confidence['before']}% → {confidence['after']}%."
        ),
    }


def compute_unlocks_from_upload(
    db: Session,
    org_id: UUID,
    current_report_id: UUID,
    findings: list[RuleFinding],
    trigger_job: IngestJob | None,
    covered_domains: set[str],
    trigger_domains: set[str] | None,
    confidence: dict,
) -> list[dict]:
    unlocks: list[dict] = []

    if confidence.get("delta", 0) > 0 and trigger_job and trigger_job.report_type:
        label = REPORT_TYPE_LABELS.get(trigger_job.report_type, trigger_job.report_type)
        unlocks.append(
            {
                "type": "confidence_increase",
                "message": (
                    f"{label} increased analysis confidence to {confidence['after']}% "
                    f"(+{confidence['delta']} points)."
                ),
            }
        )

    if trigger_domains and len(covered_domains) > len(trigger_domains or set()):
        added = covered_domains - (trigger_domains or set())
        if added:
            unlocks.append(
                {
                    "type": "org_context_expanded",
                    "message": (
                        f"Org-wide synthesis now includes {', '.join(sorted(added))} "
                        "alongside this upload's primary analysis."
                    ),
                }
            )

    prior_report = (
        db.query(OperationalReport)
        .filter(
            OperationalReport.org_id == org_id,
            OperationalReport.id != current_report_id,
        )
        .order_by(OperationalReport.generated_at.desc())
        .first()
    )
    prior_types: set[str] = set()
    if prior_report:
        for block in (
            (prior_report.financial_findings or [])
            + (prior_report.operational_findings or [])
            + (prior_report.risk_areas or [])
        ):
            if isinstance(block, dict) and block.get("finding_type"):
                prior_types.add(block["finding_type"])

    for f in findings:
        if f.finding_type in CROSS_DOMAIN_FINDING_TYPES and f.finding_type not in prior_types:
            unlocks.append(
                {
                    "type": f.finding_type,
                    "message": f"New cross-domain insight: {f.title}",
                }
            )

    return unlocks


def build_report_contract(
    db: Session,
    org_id: UUID,
    report_id: UUID,
    trigger_job: IngestJob | None,
    job_ids: list[UUID],
    period_label: str,
    trigger_domains: set[str] | None,
    primary_digest: DataDigest,
    primary_insights: list[DomainInsight],
    findings: list[RuleFinding],
    executive_summary: list[str],
    covered_domains: set[str],
    org_digest: DataDigest | None,
    org_insights: list[DomainInsight] | None,
    cross_domain_findings: list[RuleFinding],
) -> dict:
    trace = build_source_traceability(
        trigger_job,
        period_label,
        _digest_row_count(primary_digest),
    )
    primary_insight_dicts = _attach_source_to_insights(
        [i.to_dict() for i in primary_insights],
        trace,
    )
    sorted_insights = sort_domain_insights(primary_insight_dicts)

    graph_coverage = get_graph_coverage(db, org_id)
    gap_specs = _gap_specs(graph_coverage, findings)
    open_gaps = get_open_gaps(db, org_id)
    coverage_gaps = [
        {
            "gap_type": g.gap_type,
            "reason": g.reason,
            "recommended_uploads": list(g.recommended_uploads or []),
        }
        for g in open_gaps
    ]

    confidence = compute_confidence_delta(db, org_id, trigger_job)
    coverage_delta = build_coverage_delta(trigger_job, confidence)

    org_wide_synthesis = None
    if org_digest and covered_domains and (
        not trigger_domains or len(covered_domains) > len(trigger_domains)
    ):
        org_trace = {
            "source_label": (
                f"Based on: org-wide synthesis · {period_label} · "
                f"{', '.join(sorted(covered_domains))} domains"
            )
        }
        synthesis_insights = _attach_source_to_insights(
            [i.to_dict() for i in (org_insights or [])],
            org_trace,
        )
        org_wide_synthesis = {
            "org_context_domains": sorted(covered_domains),
            "digest": org_digest.to_dict(),
            "synthesis_insights": sort_domain_insights(synthesis_insights),
            "cross_domain_findings": [f.to_dict() for f in cross_domain_findings],
        }

    unlocks = compute_unlocks_from_upload(
        db,
        org_id,
        report_id,
        findings,
        trigger_job,
        covered_domains,
        trigger_domains,
        confidence,
    )

    top_signals = build_top_signals(findings, sorted_insights, executive_summary, limit=3)
    action_items = build_action_items(findings, gap_specs)

    triggered_by = sorted(trigger_domains) if trigger_domains else []

    return {
        "top_signals": top_signals,
        "action_items": action_items,
        "digest_kpis": primary_digest.to_dict(),
        "domain_insights": sorted_insights,
        "primary_analysis": {
            "triggered_by": triggered_by,
            "digest": primary_digest.to_dict(),
            "domain_insights": sorted_insights,
            "source_traceability": trace,
        },
        "org_wide_synthesis": org_wide_synthesis,
        "coverage_gaps": coverage_gaps,
        "unlocks_from_this_upload": unlocks,
        "source_traceability": trace,
        "confidence_score": confidence,
        "coverage_delta": coverage_delta,
    }


def _digest_row_count(digest: DataDigest) -> int:
    return max(
        digest.ar_invoice_count,
        digest.vendor_count,
        digest.gl_txn_count,
        digest.inventory_item_count,
    )
