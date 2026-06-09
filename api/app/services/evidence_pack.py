from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    EvidencePackRecord,
    HealthSnapshot,
    IngestJob,
    OperationalFinding,
    OperationalMemory,
    OperationalReport,
    OperationalSnapshot,
    Organization,
)
from app.schemas.evidence_pack import (
    EVIDENCE_PACK_SCHEMA_VERSION,
    EvidencePack,
    EvidencePackAnalysisBoundaries,
    EvidencePackConfidence,
    EvidencePackConfidenceComponents,
    EvidencePackCoverage,
    EvidencePackDataGap,
    EvidencePackDataQuality,
    EvidencePackEntity,
    EvidencePackFinding,
    EvidencePackHealth,
    EvidencePackHealthComponents,
    EvidencePackLockedCapability,
    EvidencePackMemory,
    EvidencePackTopEntities,
    EvidencePackTrendDelta,
)
from app.services.digest import DataDigest, build_data_digest
from app.services.gaps import gap_specs_for_report
from app.services.graph.confidence import compute_analysis_confidence
from app.services.graph.coverage import COVERAGE_SPECS, get_graph_coverage
from app.services.health import get_prior_snapshot
from app.services.progress import get_org_progress
from app.services.rules.finding_registry import FINDING_REGISTRY
from app.services.rules.types import RuleFinding
from app.services.sectors import CAPABILITIES, SECTORS
from app.services.transforms.snapshot import get_prior_snapshot as get_prior_op_snapshot


def _namespaced_metrics(digest: DataDigest) -> dict:
    top_customer = digest.top_customers[0] if digest.top_customers else None
    top_vendor = digest.top_vendors[0] if digest.top_vendors else None
    orphan_pct = (
        (digest.inventory_orphan_count / digest.inventory_item_count * 100)
        if digest.inventory_item_count
        else 0.0
    )
    zero_pct = (
        (digest.inventory_zero_count / digest.inventory_item_count * 100)
        if digest.inventory_item_count
        else 0.0
    )
    return {
        "ar": {
            "total_receivables": digest.ar_total,
            "over_90_amount": digest.ar_over_90,
            "over_90_percent": digest.ar_over_90_pct,
            "invoice_count": digest.ar_invoice_count,
            "top_customer": {
                "name": top_customer.label if top_customer else None,
                "amount": top_customer.amount if top_customer else 0,
                "percent_of_total": top_customer.pct if top_customer else 0,
            },
        },
        "ap": {
            "total_payables": digest.ap_total,
            "negative_balance_total": digest.ap_negative_total,
            "vendor_count": digest.vendor_count,
            "top_vendor": {
                "name": top_vendor.label if top_vendor else None,
                "amount": top_vendor.amount if top_vendor else 0,
                "percent_of_total": top_vendor.pct if top_vendor else 0,
            },
        },
        "gl": {
            "transaction_count": digest.gl_txn_count,
            "adjustment_total": digest.gl_adjustment_total,
            "unmapped_count": digest.gl_unmapped_count,
        },
        "inventory": {
            "item_count": digest.inventory_item_count,
            "total_units": digest.inventory_total_qty,
            "negative_count": digest.inventory_negative_count,
            "zero_stock_count": digest.inventory_zero_count,
            "zero_stock_percent": round(zero_pct, 1),
            "orphan_count": digest.inventory_orphan_count,
            "orphan_percent": round(orphan_pct, 1),
        },
    }


def _sector_coverage(coverage) -> dict[str, bool]:
    sector_keys = {
        "financials": ["ar_aging", "ap_aging", "gl_detail"],
        "manufacturing": ["inventory"],
        "orders": ["purchase_orders"],
        "sales": ["sales_orders"],
    }
    return {sector: any(coverage.has(k) for k in keys) for sector, keys in sector_keys.items()}


def _domain_coverage(coverage) -> dict[str, bool]:
    return {spec["key"]: coverage.has(spec["key"]) for spec in COVERAGE_SPECS}


def _mapping_quality(db: Session, org_id: UUID, period: str) -> float:
    jobs = (
        db.query(IngestJob)
        .filter(
            IngestJob.org_id == org_id,
            IngestJob.status == "done",
            IngestJob.detected_period == period,
            IngestJob.mapping_confidence.isnot(None),
        )
        .all()
    )
    if not jobs:
        jobs = (
            db.query(IngestJob)
            .filter(
                IngestJob.org_id == org_id,
                IngestJob.status == "done",
                IngestJob.mapping_confidence.isnot(None),
            )
            .all()
        )
    if not jobs:
        return 0.0
    return sum(j.mapping_confidence or 0 for j in jobs) / len(jobs)


def _coverage_completeness(coverage) -> float:
    uploadable = [s for s in COVERAGE_SPECS if s.get("uploadable")]
    if not uploadable:
        return 0.0
    covered = sum(1 for s in uploadable if coverage.has(s["key"]))
    return covered / len(uploadable)


def _cross_domain_joinability(coverage) -> float:
    score = 0.0
    pairs = [
        ("ar_aging", "ap_aging"),
        ("ar_aging", "inventory"),
        ("inventory", "gl_detail"),
        ("inventory", "sales_orders"),
    ]
    for a, b in pairs:
        if coverage.has(a) and coverage.has(b):
            score += 0.25
    return min(1.0, score)


def _temporal_depth(db: Session, org_id: UUID) -> float:
    count = (
        db.query(func.count(func.distinct(OperationalSnapshot.period)))
        .filter(OperationalSnapshot.org_id == org_id)
        .scalar()
        or 0
    )
    if count >= 2:
        return 1.0
    if count == 1:
        return 0.33
    return 0.0


def _build_confidence(db: Session, org_id: UUID, period: str, coverage) -> EvidencePackConfidence:
    legacy = compute_analysis_confidence(coverage)
    components = EvidencePackConfidenceComponents(
        coverage_completeness=round(_coverage_completeness(coverage), 2),
        mapping_quality=round(_mapping_quality(db, org_id, period), 2),
        cross_domain_joinability=round(_cross_domain_joinability(coverage), 2),
        temporal_depth=round(_temporal_depth(db, org_id), 2),
    )
    normalized = (
        0.40 * components.coverage_completeness
        + 0.25 * components.mapping_quality
        + 0.20 * components.cross_domain_joinability
        + 0.15 * components.temporal_depth
    )
    return EvidencePackConfidence(
        legacy_score=legacy.score,
        normalized_score=round(normalized, 2),
        components=components,
    )


def _build_analysis_boundaries(coverage, data_gaps: list[EvidencePackDataGap]) -> EvidencePackAnalysisBoundaries:
    can: list[str] = []
    cannot: list[str] = []

    if coverage.has("ar_aging"):
        can.extend(["AR aging risk", "customer concentration"])
    if coverage.has("ap_aging"):
        can.append("vendor concentration")
    if coverage.has("inventory"):
        can.append("inventory data quality")
    if coverage.has("gl_detail"):
        can.append("GL adjustment patterns")

    if not coverage.has("sales_orders"):
        cannot.append("inventory demand alignment without sales orders")
    if not coverage.has("work_orders"):
        cannot.append("WIP exposure without work orders")
    if not coverage.has("gl_detail"):
        cannot.append("margin impact without GL detail")
    if not coverage.has("ap_aging") and coverage.has("ar_aging"):
        cannot.append("working capital balance without AP aging")
    if not coverage.has("purchase_orders"):
        cannot.append("procurement dependency without purchase orders")

    for gap in data_gaps:
        if gap.reason_code == "orphan_inventory" and gap.upload not in cannot:
            cannot.append(f"financial statement inventory impact without {gap.upload}")

    return EvidencePackAnalysisBoundaries(
        can_conclude=sorted(set(can)),
        cannot_conclude=sorted(set(cannot)),
    )


def _locked_capabilities(org_progress: dict) -> list[EvidencePackLockedCapability]:
    unlocked = set(org_progress.get("unlocked_capabilities") or [])
    locked: list[EvidencePackLockedCapability] = []
    for cap in CAPABILITIES:
        cap_id = str(cap["id"])
        if cap_id in unlocked:
            continue
        required = cap.get("requires_sectors")
        if required:
            locked.append(
                EvidencePackLockedCapability(
                    capability=cap_id,
                    requires_sector=str(required[0]),
                )
            )
        elif cap.get("requires_min_sectors"):
            locked.append(
                EvidencePackLockedCapability(
                    capability=cap_id,
                    requires_sectors=int(cap["requires_min_sectors"]),  # type: ignore[arg-type]
                )
            )
    return locked


def _finding_domain(finding_type: str) -> str:
    spec = FINDING_REGISTRY.get(finding_type)
    if spec:
        return spec.domain
    return "operational"


def _tags_for_finding(finding: RuleFinding | OperationalFinding) -> list[str]:
    tags = []
    if hasattr(finding, "category") and finding.category:
        tags.append(str(finding.category))
    if hasattr(finding, "business_impact") and finding.business_impact:
        tags.append(str(finding.business_impact))
    return tags


def _build_memory_section(db: Session, org_id: UUID) -> EvidencePackMemory:
    rows = (
        db.query(OperationalMemory)
        .filter(OperationalMemory.org_id == org_id, OperationalMemory.occurrence_count > 1)
        .order_by(OperationalMemory.last_seen_at.desc())
        .limit(20)
        .all()
    )
    if not rows:
        return EvidencePackMemory(enabled=False, recurring_findings=[])

    from app.services.rules.finding_registry import FINDING_REGISTRY

    recurring = []
    for mem in rows:
        spec = FINDING_REGISTRY.get(mem.finding_type)
        recurring.append(
            {
                "finding_id": spec.finding_id if spec else None,
                "finding_type": mem.finding_type,
                "title": mem.title,
                "periods_seen": mem.occurrence_count,
                "first_seen": mem.first_seen_at.strftime("%Y-%m") if mem.first_seen_at else None,
                "last_seen": mem.last_seen_at.strftime("%Y-%m") if mem.last_seen_at else None,
            }
        )
    return EvidencePackMemory(enabled=True, recurring_findings=recurring)


def build_evidence_pack(
    db: Session,
    report_id: UUID,
    findings: list[RuleFinding] | None = None,
) -> EvidencePack:
    """Assemble immutable snapshot entirely from Postgres — no LLM, no raw rows."""
    report = db.get(OperationalReport, report_id)
    if not report:
        raise ValueError(f"Report not found: {report_id}")

    org = db.get(Organization, report.org_id)
    org_name = org.name if org else "Organization"
    period = report.period_label or datetime.now(timezone.utc).strftime("%Y-%m")

    job_ids = [UUID(j) for j in (report.job_ids or []) if j]
    coverage_graph = get_graph_coverage(db, report.org_id)
    digest = build_data_digest(
        db,
        report.org_id,
        period=period,
        source_job_ids=job_ids or None,
    )

    db_findings = (
        db.query(OperationalFinding)
        .filter(OperationalFinding.report_id == report_id)
        .all()
    )
    evidence_by_instance = {
        f.finding_instance_id: f.evidence for f in (findings or []) if f.finding_instance_id
    }
    source_keys_by_instance = {
        f.finding_instance_id: f.source_metric_keys for f in (findings or []) if f.finding_instance_id
    }
    rule_findings = findings or [
        RuleFinding(
            finding_type=f.finding_type,
            title=f.title,
            detail=f.detail,
            severity=f.severity,
            confidence=f.confidence,
            business_impact=f.business_impact,
            department=f.department,
            category=f.category,
            suggested_action=f.suggested_action or "",
            finding_id=f.finding_id or "",
            finding_instance_id=f.finding_instance_id or "",
        )
        for f in db_findings
    ]

    gap_specs = gap_specs_for_report(coverage_graph, rule_findings)
    data_gaps = [
        EvidencePackDataGap(
            upload=spec.recommended_uploads[0] if spec.recommended_uploads else spec.gap_type,
            confidence_lift=round(
                (compute_analysis_confidence(coverage_graph).score + 10) / 100, 2
            ),
            reason_code=spec.gap_type,
            priority=spec.priority,
        )
        for spec in gap_specs
    ]

    health_snap = (
        db.query(HealthSnapshot)
        .filter(HealthSnapshot.report_id == report_id)
        .order_by(HealthSnapshot.computed_at.desc())
        .first()
    )
    prior_health = None
    if health_snap:
        prior_health = get_prior_snapshot(db, report.org_id, exclude_id=health_snap.id)

    prior_op = get_prior_op_snapshot(db, report.org_id, exclude_period=period)
    prior_period = prior_op.period if prior_op else None

    health_components = EvidencePackHealthComponents()
    if health_snap and health_snap.components:
        health_components = EvidencePackHealthComponents(
            ar_risk=health_snap.components.get("ar_risk"),
            cash_flow=health_snap.components.get("cash_flow"),
            inventory=health_snap.components.get("inventory"),
            data_quality=health_snap.components.get("data_quality"),
        )

    health_delta = None
    if health_snap and prior_health:
        health_delta = health_snap.score - prior_health.score

    trend_deltas: list[EvidencePackTrendDelta] = []
    if health_snap and prior_health and health_delta is not None:
        direction = "improved" if health_delta > 0 else ("declined" if health_delta < 0 else "stable")
        trend_deltas.append(
            EvidencePackTrendDelta(
                metric="health_score",
                prior=prior_health.score,
                current=health_snap.score,
                delta=health_delta,
                direction=direction,
            )
        )

    sectors = _sector_coverage(coverage_graph)
    sectors_count = sum(1 for s in SECTORS if sectors.get(s))

    mapping_warnings: list[str] = []
    low_confidence: list[dict] = []
    failed_uploads: list[dict[str, str]] = []
    for job in db.query(IngestJob).filter(IngestJob.org_id == report.org_id).all():
        if job.status == "error" and job.errors:
            for err in job.errors[:3]:
                if isinstance(err, dict):
                    failed_uploads.append(
                        {
                            "filename": job.file_name,
                            "error": str(err.get("code") or err.get("message") or "upload_error"),
                        }
                    )
        meta = job.mapping_metadata or {}
        for w in meta.get("warnings") or []:
            if isinstance(w, str):
                mapping_warnings.append(w)
        if job.mapping_confidence is not None and job.mapping_confidence < 0.75:
            low_confidence.append(
                {
                    "filename": job.file_name,
                    "confidence": job.mapping_confidence,
                }
            )

    pack_findings: list[EvidencePackFinding] = []
    finding_rows = db_findings if db_findings else []
    if not finding_rows and findings:
        for f in findings:
            pack_findings.append(
                EvidencePackFinding(
                    finding_id=f.finding_id,
                    finding_instance_id=f.finding_instance_id,
                    title=f.title,
                    severity=f.severity,
                    domain=_finding_domain(f.finding_type),
                    tags=_tags_for_finding(f),
                    evidence=f.evidence,
                    source_metric_keys=list(f.source_metric_keys),
                    deterministic_action=f.suggested_action,
                )
            )
    else:
        for f in finding_rows:
            instance_id = f.finding_instance_id or ""
            evidence = evidence_by_instance.get(instance_id, {})
            source_keys = source_keys_by_instance.get(instance_id) or (
                list(FINDING_REGISTRY[f.finding_type].source_metric_keys)
                if f.finding_type in FINDING_REGISTRY
                else []
            )
            pack_findings.append(
                EvidencePackFinding(
                    finding_id=f.finding_id or "",
                    finding_instance_id=instance_id,
                    title=f.title,
                    severity=f.severity,
                    domain=_finding_domain(f.finding_type),
                    tags=_tags_for_finding(f),
                    evidence=evidence,
                    source_metric_keys=source_keys,
                    deterministic_action=f.suggested_action,
                )
            )

    top_entities = EvidencePackTopEntities(
        customers=[
            EvidencePackEntity(name=t.label, amount=t.amount, pct_of_total=t.pct)
            for t in digest.top_customers[:5]
        ],
        vendors=[
            EvidencePackEntity(name=t.label, amount=t.amount, pct_of_total=t.pct)
            for t in digest.top_vendors[:5]
        ],
    )

    org_progress = get_org_progress(db, report.org_id)
    confidence = _build_confidence(db, report.org_id, period, coverage_graph)
    analysis_boundaries = _build_analysis_boundaries(coverage_graph, data_gaps)

    return EvidencePack(
        schema_version=EVIDENCE_PACK_SCHEMA_VERSION,
        agent_ready=True,
        agent_input_type=EVIDENCE_PACK_SCHEMA_VERSION,
        raw_data_included=False,
        org_id=str(report.org_id),
        org_name=org_name,
        period=period,
        generated_at=datetime.now(timezone.utc),
        prior_period=prior_period,
        coverage=EvidencePackCoverage(
            sectors=sectors,
            domains=_domain_coverage(coverage_graph),
            sectors_count=sectors_count,
            sectors_total=len(SECTORS),
        ),
        confidence=confidence,
        health=EvidencePackHealth(
            score=health_snap.score if health_snap else report.health_score,
            status=health_snap.status if health_snap else report.health_status,
            components=health_components,
            prior_score=prior_health.score if prior_health else None,
            delta=health_delta,
        ),
        metrics=_namespaced_metrics(digest),
        top_entities=top_entities,
        findings=pack_findings,
        trend_deltas=trend_deltas,
        data_gaps=data_gaps,
        data_quality=EvidencePackDataQuality(
            mapping_warnings=mapping_warnings,
            failed_uploads=failed_uploads,
            low_confidence_mappings=low_confidence,
        ),
        analysis_boundaries=analysis_boundaries,
        memory=_build_memory_section(db, report.org_id),
        locked_capabilities=_locked_capabilities(org_progress),
    )


def persist_evidence_pack(db: Session, report_id: UUID, pack: EvidencePack) -> EvidencePackRecord:
    report = db.get(OperationalReport, report_id)
    if not report:
        raise ValueError(f"Report not found: {report_id}")

    existing = (
        db.query(EvidencePackRecord)
        .filter(EvidencePackRecord.report_id == report_id)
        .first()
    )
    pack_dict = pack.model_dump(mode="json")
    if existing:
        existing.pack = pack_dict
        existing.schema_version = pack.schema_version
        existing.period_label = report.period_label or pack.period
        db.flush()
        return existing

    row = EvidencePackRecord(
        report_id=report_id,
        org_id=report.org_id,
        period_label=report.period_label or pack.period,
        pack=pack_dict,
        schema_version=pack.schema_version,
    )
    db.add(row)
    db.flush()
    return row


def get_evidence_pack_for_report(db: Session, report_id: UUID) -> dict | None:
    row = (
        db.query(EvidencePackRecord)
        .filter(EvidencePackRecord.report_id == report_id)
        .first()
    )
    return row.pack if row else None
