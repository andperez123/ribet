from __future__ import annotations

"""Deterministic data gap detection — Ribet tells users what to upload next."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import DataGapRequest
from app.services.graph.confidence import confidence_if_keys_added, compute_analysis_confidence
from app.services.graph.coverage import GraphCoverage, get_graph_coverage
from app.services.rules.runner import RuleFinding


@dataclass
class GapSpec:
    gap_type: str
    reason: str
    recommended_uploads: list[str]
    requested_report_types: list[str]
    requested_sector: str
    priority: str = "medium"
    satisfied_keys: list[str] | None = None


def _gap_specs(
    coverage: GraphCoverage,
    findings: list[RuleFinding],
) -> list[GapSpec]:
    specs: list[GapSpec] = []
    finding_types = {f.finding_type for f in findings}

    if coverage.has("ar_aging") and not coverage.has("ap_aging"):
        specs.append(
            GapSpec(
                gap_type="missing_ap_aging",
                reason=(
                    "AR aging is uploaded but AP aging is missing. "
                    "Ribet cannot compare receivables vs payables without AP data."
                ),
                recommended_uploads=["AP Aging"],
                requested_report_types=["ap_aging"],
                requested_sector="financials",
                priority="high",
                satisfied_keys=["ap_aging"],
            )
        )

    if "ar_aging_spike" in finding_types and not coverage.has("invoice_detail"):
        specs.append(
            GapSpec(
                gap_type="missing_invoice_detail",
                reason=(
                    "Elevated AR over 90 days detected. "
                    "Invoice detail would help identify customer-specific collection risk."
                ),
                recommended_uploads=["Invoice Detail"],
                requested_report_types=["invoice_detail"],
                requested_sector="financials",
                priority="medium",
                satisfied_keys=["invoice_detail"],
            )
        )

    if coverage.has("inventory") and not coverage.has("sales_orders"):
        specs.append(
            GapSpec(
                gap_type="missing_sales_orders",
                reason=(
                    "Inventory data is present without open sales orders. "
                    "Ribet cannot assess whether inventory levels match demand."
                ),
                recommended_uploads=["Open Sales Orders"],
                requested_report_types=["sales_orders"],
                requested_sector="sales",
                priority="medium",
                satisfied_keys=["sales_orders"],
            )
        )

    if coverage.has("inventory") and any(
        ft in finding_types for ft in ("inventory_adjustment_spike", "orphan_inventory")
    ) and not coverage.has("work_orders"):
        specs.append(
            GapSpec(
                gap_type="missing_work_orders",
                reason=(
                    "Inventory adjustments or mapping issues detected. "
                    "Work order or labor exports would help trace root causes."
                ),
                recommended_uploads=["Work Order Export", "Labor Detail"],
                requested_report_types=["work_orders"],
                requested_sector="manufacturing",
                priority="medium",
                satisfied_keys=["work_orders"],
            )
        )

    if coverage.has("ap_aging") and "vendor_concentration" in finding_types and not coverage.has(
        "purchase_orders"
    ):
        specs.append(
            GapSpec(
                gap_type="missing_purchase_orders",
                reason=(
                    "Vendor concentration risk detected in AP. "
                    "Purchase order data would clarify procurement dependency."
                ),
                recommended_uploads=["Purchase Orders"],
                requested_report_types=["purchase_orders"],
                requested_sector="orders",
                priority="medium",
                satisfied_keys=["purchase_orders"],
            )
        )

    if "operational_cash_pressure" in finding_types:
        specs.append(
            GapSpec(
                gap_type="cash_pressure_diagnosis",
                reason=(
                    "AR and inventory signals are both elevated. "
                    "Upload AP Aging, Open Sales Orders, and Purchase Orders "
                    "to determine whether cash is trapped in operations."
                ),
                recommended_uploads=["AP Aging", "Open Sales Orders", "Purchase Orders"],
                requested_report_types=["ap_aging", "sales_orders", "purchase_orders"],
                requested_sector="financials",
                priority="high",
                satisfied_keys=["ap_aging", "sales_orders", "purchase_orders"],
            )
        )

    return specs


def _is_satisfied(spec: GapSpec, coverage: GraphCoverage) -> bool:
    if spec.satisfied_keys:
        return all(coverage.has(k) for k in spec.satisfied_keys)
    if spec.requested_report_types:
        return all(coverage.has_report_type(rt) for rt in spec.requested_report_types)
    return False


def gap_specs_for_report(
    coverage: GraphCoverage,
    findings: list[RuleFinding],
) -> list[GapSpec]:
    """Public wrapper for evidence pack and contract builders."""
    return _gap_specs(coverage, findings)


def sync_data_gaps(
    db: Session,
    org_id: UUID,
    coverage: GraphCoverage | None = None,
    findings: list[RuleFinding] | None = None,
) -> list[DataGapRequest]:
    coverage = coverage or get_graph_coverage(db, org_id)
    findings = findings or []
    confidence = compute_analysis_confidence(coverage)
    now = datetime.now(timezone.utc)

    active_types = {s.gap_type for s in _gap_specs(coverage, findings)}

    open_rows = (
        db.query(DataGapRequest)
        .filter(DataGapRequest.org_id == org_id, DataGapRequest.status == "open")
        .all()
    )
    for row in open_rows:
        spec_match = next((s for s in _gap_specs(coverage, findings) if s.gap_type == row.gap_type), None)
        if spec_match and _is_satisfied(spec_match, coverage):
            row.status = "satisfied"
            row.updated_at = now
        elif row.gap_type not in active_types:
            row.status = "satisfied"
            row.updated_at = now

    result: list[DataGapRequest] = []
    for spec in _gap_specs(coverage, findings):
        if _is_satisfied(spec, coverage):
            continue

        lift_keys = spec.satisfied_keys or []
        if lift_keys:
            conf_lift = confidence_if_keys_added(coverage, lift_keys[:1])
        else:
            conf_lift = min(100, confidence.score + 10)

        existing = (
            db.query(DataGapRequest)
            .filter(
                DataGapRequest.org_id == org_id,
                DataGapRequest.gap_type == spec.gap_type,
                DataGapRequest.status == "open",
            )
            .first()
        )
        if existing:
            existing.reason = spec.reason
            existing.recommended_uploads = spec.recommended_uploads
            existing.requested_report_types = spec.requested_report_types
            existing.requested_sector = spec.requested_sector
            existing.confidence_if_uploaded = conf_lift
            existing.priority = spec.priority
            existing.updated_at = now
            result.append(existing)
        else:
            row = DataGapRequest(
                org_id=org_id,
                gap_type=spec.gap_type,
                reason=spec.reason,
                recommended_uploads=spec.recommended_uploads,
                requested_report_types=spec.requested_report_types,
                requested_sector=spec.requested_sector,
                confidence_if_uploaded=conf_lift,
                priority=spec.priority,
                status="open",
            )
            db.add(row)
            result.append(row)

    db.flush()
    return result


def get_open_gaps(db: Session, org_id: UUID) -> list[DataGapRequest]:
    return (
        db.query(DataGapRequest)
        .filter(DataGapRequest.org_id == org_id, DataGapRequest.status == "open")
        .order_by(DataGapRequest.priority.desc(), DataGapRequest.created_at.desc())
        .all()
    )
