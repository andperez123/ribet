from __future__ import annotations

"""Deterministic analyst output when AI verification fails."""

from app.schemas.analyst_output import (
    AnalystOutput,
    ConditionalInsight,
    DashboardBriefing,
    DashboardExplanations,
    DomainInsightsOutput,
    ManagementQuestion,
    MetricTakeaway,
    RecommendedUpload,
    TopRisk,
    WhatChangedItem,
)
from app.schemas.evidence_pack import EvidencePack

_SEVERITY_IMPACT = {"critical": "high", "high": "high", "medium": "medium", "low": "low"}


def _briefing_tone(pack: EvidencePack, top_risks: list[TopRisk]) -> str:
    if any(r.impact == "high" for r in top_risks):
        return "critical"
    if pack.findings:
        return "caution"
    if pack.health.score >= 85:
        return "positive"
    return "neutral"


def _build_dashboard_briefing(
    pack: EvidencePack,
    executive: list[str],
    top_risks: list[TopRisk],
    recommended_uploads: list[RecommendedUpload],
) -> DashboardBriefing:
    headline = executive[0] if executive else (
        f"Operational health is {pack.health.status.lower()} at {pack.health.score}/100."
    )
    narrative = " ".join(executive[1:3]) if len(executive) > 1 else ""
    focus = ""
    if top_risks:
        focus = top_risks[0].recommended_action
    elif recommended_uploads:
        focus = f"Upload {recommended_uploads[0].upload} to expand analysis."
    return DashboardBriefing(
        headline=headline,
        narrative=narrative,
        focus=focus,
        tone=_briefing_tone(pack, top_risks),  # type: ignore[arg-type]
    )


def _build_metric_takeaways(pack: EvidencePack, top_risks: list[TopRisk]) -> list[MetricTakeaway]:
    takeaways: list[MetricTakeaway] = []
    ar = pack.metrics.get("ar", {})
    ap = pack.metrics.get("ap", {})
    inv = pack.metrics.get("inventory", {})
    gl = pack.metrics.get("gl", {})
    top_finding_ids = [f.finding_id for f in pack.findings[:1] if f.finding_id]

    if ar.get("total_receivables"):
        over_90 = float(ar.get("over_90_percent") or 0)
        takeaways.append(
            MetricTakeaway(
                metric_key="collections_at_risk",
                takeaway=(
                    f"Review collections — {over_90:.1f}% of AR is over 90 days. "
                    "Prioritize follow-up with accounts driving the largest balances."
                ),
                finding_ids=top_finding_ids,
            )
        )
        customers = pack.top_entities.customers
        if customers:
            top = customers[0]
            pct = top.pct_of_total or 0
            takeaways.append(
                MetricTakeaway(
                    metric_key="customer_concentration",
                    takeaway=(
                        f"{top.name} represents {pct:.1f}% of receivables — "
                        "monitor exposure if payment slows."
                    ),
                    finding_ids=top_finding_ids,
                )
            )

    if ap.get("total_payables"):
        over_60 = float(ap.get("over_60_percent") or 0)
        takeaways.append(
            MetricTakeaway(
                metric_key="payables_over_60",
                takeaway=(
                    f"{over_60:.1f}% of payables are over 60 days — "
                    "confirm cash timing with your controller."
                ),
                finding_ids=top_finding_ids,
            )
        )
        vendors = pack.top_entities.vendors
        if vendors:
            top = vendors[0]
            pct = top.pct_of_total or 0
            takeaways.append(
                MetricTakeaway(
                    metric_key="vendor_concentration",
                    takeaway=(
                        f"{top.name} is {pct:.1f}% of open AP — "
                        "review terms and delivery dependency."
                    ),
                    finding_ids=top_finding_ids,
                )
            )

    if ar.get("total_receivables") and ap.get("total_payables"):
        ar_total = float(ar.get("total_receivables") or 0)
        ap_total = float(ap.get("total_payables") or 0)
        takeaways.append(
            MetricTakeaway(
                metric_key="receivables_vs_payables",
                takeaway=(
                    f"Open AR ${ar_total:,.0f} vs AP ${ap_total:,.0f} — "
                    "use this gap to plan near-term cash needs."
                ),
                finding_ids=top_finding_ids,
            )
        )

    if inv.get("item_count"):
        orphan_pct = float(inv.get("orphan_percent") or 0)
        takeaways.append(
            MetricTakeaway(
                metric_key="inventory_readiness",
                takeaway=(
                    f"{orphan_pct:.1f}% of SKUs lack GL mapping — "
                    "fix mappings before relying on inventory financials."
                ),
                finding_ids=top_finding_ids,
            )
        )

    if gl.get("transaction_count") and not (ar.get("total_receivables") or ap.get("total_payables")):
        takeaways.append(
            MetricTakeaway(
                metric_key="gl_activity",
                takeaway=(
                    f"{int(gl.get('transaction_count') or 0)} GL transactions analyzed — "
                    "upload AR and AP aging to unlock cash-flow insights."
                ),
                finding_ids=top_finding_ids,
            )
        )

    if top_risks and not takeaways:
        takeaways.append(
            MetricTakeaway(
                metric_key="collections_at_risk",
                takeaway=top_risks[0].recommended_action,
                finding_ids=top_risks[0].finding_ids,
            )
        )

    return takeaways


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
        dashboard_briefing=_build_dashboard_briefing(
            pack, executive, top_risks, recommended_uploads
        ),
        metric_takeaways=_build_metric_takeaways(pack, top_risks),
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
