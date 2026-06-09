from __future__ import annotations

"""Deterministic analyst output when AI verification fails."""

from app.schemas.analyst_output import (
    AnalystOutput,
    ConditionalInsight,
    DashboardExplanations,
    DomainInsightsOutput,
    ManagementQuestion,
    RecommendedUpload,
    TopRisk,
    WhatChangedItem,
)
from app.schemas.evidence_pack import EvidencePack

_SEVERITY_IMPACT = {"critical": "high", "high": "high", "medium": "medium", "low": "low"}


def build_deterministic_analyst_output(pack: EvidencePack) -> AnalystOutput:
    """Build controller-grade output entirely from the evidence pack."""
    executive: list[str] = [
        f"Operational health is {pack.health.status.lower()} at {pack.health.score}/100 for {pack.period}."
    ]
    if pack.health.prior_score is not None and pack.health.delta is not None:
        direction = "improved" if pack.health.delta > 0 else "declined" if pack.health.delta < 0 else "unchanged"
        executive.append(
            f"Health score {direction} {abs(pack.health.delta)} points vs prior period "
            f"({pack.health.prior_score} → {pack.health.score})."
        )
    if pack.findings:
        executive.append(
            f"Ribet detected {len(pack.findings)} deterministic finding(s) from uploaded data."
        )
    else:
        executive.append("No rule findings triggered; review digest KPIs for monitoring signals.")

    sorted_findings = sorted(
        pack.findings,
        key=lambda f: {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(f.severity, 0),
        reverse=True,
    )
    top_risks: list[TopRisk] = []
    for i, f in enumerate(sorted_findings[:3], start=1):
        top_risks.append(
            TopRisk(
                rank=i,
                title=f.title,
                impact=_SEVERITY_IMPACT.get(f.severity, "medium"),  # type: ignore[arg-type]
                finding_ids=[f.finding_id] if f.finding_id else [],
                metric_keys=f.source_metric_keys[:3],
                narrative=f.detail,
                recommended_action=f.deterministic_action or "Review with your controller.",
            )
        )

    what_changed: list[WhatChangedItem] = []
    for delta in pack.trend_deltas:
        what_changed.append(
            WhatChangedItem(
                metric_key=delta.metric,
                narrative=(
                    f"{delta.metric} moved from {delta.prior} to {delta.current} "
                    f"({delta.direction or 'changed'})."
                ),
                finding_ids=[],
            )
        )

    management_questions: list[ManagementQuestion] = []
    for f in sorted_findings[:4]:
        management_questions.append(
            ManagementQuestion(
                question=f"What is driving: {f.title}?",
                context=f.detail[:200],
                finding_ids=[f.finding_id] if f.finding_id else [],
            )
        )

    recommended_uploads = [
        RecommendedUpload(
            upload=g.upload,
            priority=g.priority,  # type: ignore[arg-type]
            confidence_lift=g.confidence_lift,
            rationale=g.reason_code.replace("_", " ").capitalize(),
            reason_code=g.reason_code,
            finding_ids=[],
        )
        for g in pack.data_gaps[:5]
    ]

    ar = pack.metrics.get("ar", {})
    ap = pack.metrics.get("ap", {})
    inv = pack.metrics.get("inventory", {})

    dashboard = DashboardExplanations(
        ar_risk=(
            f"AR total ${ar.get('total_receivables', 0):,.0f}; "
            f"{ar.get('over_90_percent', 0):.1f}% over 90 days."
            if ar.get("total_receivables")
            else "No AR data uploaded."
        ),
        cash_flow=(
            f"Receivables ${ar.get('total_receivables', 0):,.0f}; payables ${ap.get('total_payables', 0):,.0f}."
            if ar.get("total_receivables") or ap.get("total_payables")
            else "Upload AR and AP aging for cash-flow commentary."
        ),
        inventory=(
            f"{inv.get('item_count', 0)} items; {inv.get('orphan_percent', 0):.1f}% lack GL mapping."
            if inv.get("item_count")
            else "No inventory data uploaded."
        ),
        data_quality=(
            "Mapping warnings present — review upload configuration."
            if pack.data_quality.mapping_warnings
            else "No major mapping warnings in current uploads."
        ),
    )

    confidence_notes = [
        f"Analysis confidence is {pack.confidence.normalized_score:.0%} "
        f"(legacy score {pack.confidence.legacy_score}/100)."
    ]
    if pack.analysis_boundaries.cannot_conclude:
        confidence_notes.append(
            "Ribet cannot conclude: " + "; ".join(pack.analysis_boundaries.cannot_conclude[:3]) + "."
        )

    conditional = [
        ConditionalInsight(
            locked_capability=cap.capability,
            requires_upload=cap.requires_sector or f"{cap.requires_sectors} sectors",
            insight=f"Upload data to unlock {cap.capability.replace('_', ' ')} insights.",
            finding_ids=[],
        )
        for cap in pack.locked_capabilities[:3]
    ]

    recurring = pack.memory.recurring_findings if pack.memory.enabled else []
    if recurring:
        executive.append(
            f"{len(recurring)} recurring finding(s) detected across prior periods."
        )

    return AnalystOutput(
        executive_summary=executive,
        top_risks=top_risks,
        what_changed=what_changed,
        management_questions=management_questions,
        recommended_uploads=recommended_uploads,
        dashboard_explanations=dashboard,
        domain_insights=DomainInsightsOutput(
            controller=dashboard.ar_risk + " " + dashboard.cash_flow,
            inventory=dashboard.inventory,
            data_quality=dashboard.data_quality,
        ),
        confidence_notes=confidence_notes,
        conditional_insights=conditional,
        source="deterministic_fallback",
    )
