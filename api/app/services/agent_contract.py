from __future__ import annotations

"""Agent roster, blocked analyses, and evidence summary for report contract."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas.evidence_pack import EVIDENCE_PACK_SCHEMA_VERSION, EvidencePack
from app.services.ai_analyst.runner import AnalystResult
from app.services.digest import DataDigest
from app.services.gaps import _gap_specs, get_open_gaps
from app.services.graph.coverage import get_graph_coverage
from app.services.report_contract import REPORT_TYPE_LABELS, build_source_traceability
from app.services.rules.runner import RuleFinding

BLOCKED_ANALYSIS_MAP: dict[str, tuple[str, list[str]]] = {
    "missing_sales_orders": ("Inventory vs Demand", ["Open Sales Orders"]),
    "missing_work_orders": ("Production Bottleneck Detection", ["Work Orders"]),
    "missing_purchase_orders": ("Vendor Fulfillment Analysis", ["Purchase Orders"]),
    "missing_ap_aging": ("Working Capital View", ["AP Aging"]),
    "missing_invoice_detail": ("Customer Collection Risk", ["Invoice Detail"]),
    "cash_pressure_diagnosis": (
        "Cash Pressure Diagnosis",
        ["AP Aging", "Open Sales Orders", "Purchase Orders"],
    ),
}

GATED_UNLOCK_MESSAGES: list[tuple[str, str]] = [
    ("cross_sector", "Cross-sector insights (need 3 sectors)"),
    ("demand_match", "Demand match (need Open Sales Orders)"),
    ("gl_reconciliation", "GL reconciliation (need GL Detail)"),
]


def build_blocked_analyses(
    db: Session,
    org_id: UUID,
    findings: list[RuleFinding],
    coverage: dict[str, bool],
) -> list[dict]:
    graph_coverage = get_graph_coverage(db, org_id)
    analyses: list[dict] = []
    seen: set[str] = set()

    for spec in _gap_specs(graph_coverage, findings):
        mapped = BLOCKED_ANALYSIS_MAP.get(spec.gap_type)
        if mapped:
            name, default_uploads = mapped
            if name in seen:
                continue
            seen.add(name)
            analyses.append(
                {
                    "analysis_name": name,
                    "reason": spec.reason,
                    "requires_uploads": spec.recommended_uploads or default_uploads,
                }
            )

    if not coverage.get("gl") and "Margin Leakage Analysis" not in seen:
        analyses.append(
            {
                "analysis_name": "Margin Leakage Analysis",
                "reason": "GL detail is required to reconcile margins and adjustments.",
                "requires_uploads": ["GL Detail"],
            }
        )

    open_gaps = get_open_gaps(db, org_id)
    for gap in open_gaps:
        mapped = BLOCKED_ANALYSIS_MAP.get(gap.gap_type)
        if not mapped:
            continue
        name, default_uploads = mapped
        if name in seen:
            continue
        seen.add(name)
        analyses.append(
            {
                "analysis_name": name,
                "reason": gap.reason,
                "requires_uploads": list(gap.recommended_uploads or default_uploads),
            }
        )

    return analyses


def build_evidence_summary(
    pack: EvidencePack | None,
    digest: DataDigest,
    coverage: dict[str, bool],
    findings_count: int,
    confidence_score: int | None,
) -> dict:
    sources: list[dict] = []
    if coverage.get("ar") and digest.ar_invoice_count > 0:
        sources.append(
            {
                "label": "AR Aging",
                "detail": f"{digest.ar_invoice_count:,} invoices analyzed",
            }
        )
    if coverage.get("ap") and digest.vendor_count > 0:
        sources.append(
            {
                "label": "AP Aging",
                "detail": f"{digest.vendor_count:,} vendor balances analyzed",
            }
        )
    if coverage.get("gl") and digest.gl_txn_count > 0:
        sources.append(
            {
                "label": "GL Detail",
                "detail": f"{digest.gl_txn_count:,} transactions analyzed",
            }
        )
    if coverage.get("inventory") and digest.inventory_item_count > 0:
        sources.append(
            {
                "label": "Inventory",
                "detail": f"{digest.inventory_item_count:,} SKUs analyzed",
            }
        )

    domain_count = sum(1 for k in ("ar", "ap", "gl", "inventory") if coverage.get(k))
    metric_count = len(pack.metrics) if pack else 0
    pack_findings = len(pack.findings) if pack else findings_count

    return {
        "schema_version": pack.schema_version if pack else EVIDENCE_PACK_SCHEMA_VERSION,
        "generated_at": pack.generated_at.isoformat() if pack else None,
        "metric_count": metric_count,
        "finding_count": pack_findings,
        "coverage_domains": domain_count,
        "confidence_score": confidence_score,
        "rules_executed": findings_count,
        "sources": sources,
    }


def build_agent_roster(
    coverage: dict[str, bool],
    blocked_analyses: list[dict],
    analyst_result: AnalystResult | None,
    digest: DataDigest,
    sectors_covered: set[str] | None = None,
) -> list[dict]:
    sectors_covered = sectors_covered or set()
    now = datetime.now(timezone.utc).isoformat()
    duration_ms = analyst_result.duration_ms if analyst_result else None
    pack_version = EVIDENCE_PACK_SCHEMA_VERSION

    def entry(
        agent: str,
        domain_scope: str,
        status: str,
        status_message: str,
        *,
        completed: bool = False,
    ) -> dict:
        return {
            "agent": agent,
            "domain_scope": domain_scope,
            "status": status,
            "status_message": status_message,
            "last_completed_at": now if completed else None,
            "analysis_duration_ms": duration_ms if completed else None,
            "evidence_pack_version": pack_version if completed else None,
        }

    roster: list[dict] = []

    has_ar_ap = coverage.get("ar") or coverage.get("ap")
    if has_ar_ap:
        msg = "AR/AP analyzed"
        if digest.ar_total > 0:
            msg = f"${digest.ar_total:,.0f} AR analyzed"
        roster.append(entry("controller", "AR · AP", "complete", msg, completed=True))
    else:
        roster.append(
            entry("controller", "AR · AP", "needs_data", "Upload AR Aging or AP Aging to activate")
        )

    if coverage.get("inventory"):
        roster.append(
            entry(
                "inventory",
                "Inventory",
                "complete",
                f"{digest.inventory_item_count:,} SKUs analyzed",
                completed=True,
            )
        )
    else:
        roster.append(
            entry("inventory", "Inventory", "needs_data", "Upload Inventory to activate")
        )

    dq_issues = digest.gl_unmapped_count > 0 or digest.inventory_orphan_count > 0
    if dq_issues:
        roster.append(
            entry(
                "data_quality",
                "Mapping · Quality",
                "needs_data",
                "Waiting: mapping or GL linkage confirmation",
            )
        )
    elif has_ar_ap or coverage.get("inventory") or coverage.get("gl"):
        roster.append(
            entry(
                "data_quality",
                "Mapping · Quality",
                "complete",
                "No critical mapping issues detected",
                completed=True,
            )
        )
    else:
        roster.append(
            entry("data_quality", "Mapping · Quality", "needs_data", "Upload data to assess quality")
        )

    if analyst_result and analyst_result.output and not analyst_result.skipped:
        roster.append(
            entry(
                "executive",
                "Synthesis",
                "complete",
                "Executive synthesis complete",
                completed=True,
            )
        )
    elif analyst_result and analyst_result.skipped:
        roster.append(
            entry("executive", "Synthesis", "needs_data", "AI narration disabled")
        )
    else:
        roster.append(
            entry("executive", "Synthesis", "needs_data", "Waiting for domain analysis")
        )

    if "orders" in sectors_covered:
        roster.append(entry("procurement", "Orders", "complete", "Orders sector covered", completed=True))
    else:
        roster.append(
            entry("procurement", "Orders", "locked", "Upload Orders sector to activate")
        )

    if coverage.get("ar") and not any(
        b.get("analysis_name") == "Inventory vs Demand" for b in blocked_analyses
    ):
        roster.append(
            entry("sales", "Sales · Demand", "locked", "Upload Open Sales Orders to activate")
        )
    elif "sales" in sectors_covered:
        roster.append(entry("sales", "Sales · Demand", "complete", "Sales data available", completed=True))
    else:
        roster.append(
            entry("sales", "Sales · Demand", "locked", "Upload Open Sales Orders to activate")
        )

    return roster


def enrich_top_signals(
    signals: list[dict],
    findings: list[RuleFinding],
    trace: dict,
    has_evidence_pack: bool,
) -> list[dict]:
    finding_by_title = {f.title: f for f in findings}
    enriched: list[dict] = []

    for signal in signals:
        row = dict(signal)
        finding = finding_by_title.get(row.get("title", ""))
        if finding:
            row["finding_id"] = finding.finding_id
            row["why_it_matters"] = finding.business_impact or finding.detail or row.get("body")
            row["source_trace"] = {
                **trace,
                "finding_id": finding.finding_id,
                "evidence_verified": has_evidence_pack and bool(finding.finding_id),
            }
        else:
            row["why_it_matters"] = row.get("body")
            if trace:
                row["source_trace"] = {**trace, "evidence_verified": has_evidence_pack}
        enriched.append(row)

    return enriched[:3]


def split_unlocks(
    unlocks: list[dict],
    blocked_analyses: list[dict],
    open_gap_count: int,
) -> dict:
    still_gated: list[dict] = []
    for _key, message in GATED_UNLOCK_MESSAGES:
        still_gated.append({"type": "gated", "message": message})

    for blocked in blocked_analyses[:3]:
        uploads = ", ".join(blocked.get("requires_uploads") or [])
        still_gated.append(
            {
                "type": "blocked_analysis",
                "message": f"{blocked['analysis_name']} (need {uploads})",
            }
        )

    if open_gap_count > 0 and not still_gated:
        still_gated.append(
            {"type": "gaps", "message": f"{open_gap_count} analysis gap(s) remain open"}
        )

    return {"unlocked": unlocks, "still_gated": still_gated}


def finalize_report_contract(
    contract: dict,
    db: Session,
    org_id: UUID,
    findings: list[RuleFinding],
    coverage: dict[str, bool],
    digest: DataDigest,
    pack: EvidencePack | None,
    analyst_result: AnalystResult | None,
    trigger_job,
    period_label: str,
) -> dict:
    trace = build_source_traceability(
        trigger_job,
        period_label,
        max(
            digest.ar_invoice_count,
            digest.vendor_count,
            digest.gl_txn_count,
            digest.inventory_item_count,
        ),
    )
    confidence = contract.get("confidence_score") or {}
    blocked = build_blocked_analyses(db, org_id, findings, coverage)
    evidence_summary = build_evidence_summary(
        pack,
        digest,
        coverage,
        len(findings),
        confidence.get("after"),
    )
    sectors: set[str] = set()
    if trigger_job and trigger_job.sector:
        sectors.add(trigger_job.sector)

    contract["blocked_analyses"] = blocked
    contract["evidence_summary"] = evidence_summary
    contract["agent_roster"] = build_agent_roster(
        coverage, blocked, analyst_result, digest, sectors
    )
    contract["top_signals"] = enrich_top_signals(
        contract.get("top_signals") or [],
        findings,
        trace,
        pack is not None,
    )

    open_gaps = get_open_gaps(db, org_id)
    raw_unlocks = contract.get("unlocks_from_this_upload") or []
    if isinstance(raw_unlocks, dict):
        unlocked = raw_unlocks.get("unlocked", [])
    else:
        unlocked = raw_unlocks
    contract["unlocks_from_this_upload"] = split_unlocks(
        unlocked, blocked, len(open_gaps)
    )

    if trace:
        contract["source_traceability"] = {
            **trace,
            "evidence_verified": pack is not None,
        }

    return contract
