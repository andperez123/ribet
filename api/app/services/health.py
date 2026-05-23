from uuid import UUID

from sqlalchemy.orm import Session

from app.models import HealthSnapshot, OperationalFinding
from app.services.rules.runner import RuleFinding

SEVERITY_PENALTY = {"low": 2, "medium": 5, "high": 12, "critical": 20}


def compute_health(
    db: Session,
    org_id: UUID,
    findings: list[RuleFinding],
    report_id: UUID | None = None,
) -> HealthSnapshot:
    base = 100
    penalty = sum(SEVERITY_PENALTY.get(f.severity, 5) for f in findings)
    score = max(0, min(100, base - penalty))

    if score >= 75:
        status = "Stable"
    elif score >= 50:
        status = "At Risk"
    else:
        status = "Critical"

    financial = [f for f in findings if f.category == "financial"]
    operational = [f for f in findings if f.category == "operational"]
    dq = [f for f in findings if f.category == "data_quality"]

    components = {
        "cash_flow": max(0, 100 - len([f for f in financial if f.business_impact == "cash_flow"]) * 15),
        "ar_risk": max(0, 100 - len([f for f in findings if f.finding_type == "ar_aging_spike"]) * 20),
        "inventory": max(0, 100 - len(operational) * 10),
        "data_quality": max(0, 100 - len(dq) * 8),
        "overall": score,
    }

    snapshot = HealthSnapshot(
        org_id=org_id,
        report_id=report_id,
        score=score,
        status=status,
        components=components,
        metadata_={"finding_count": len(findings)},
    )
    db.add(snapshot)
    db.flush()
    return snapshot


def get_prior_snapshot(db: Session, org_id: UUID, exclude_id: UUID | None = None) -> HealthSnapshot | None:
    q = db.query(HealthSnapshot).filter(HealthSnapshot.org_id == org_id)
    if exclude_id:
        q = q.filter(HealthSnapshot.id != exclude_id)
    return q.order_by(HealthSnapshot.computed_at.desc()).first()


def build_trend_snapshot(
    current: HealthSnapshot,
    prior: HealthSnapshot | None,
    findings: list[RuleFinding],
) -> list[str]:
    trends: list[str] = []
    if prior:
        delta = current.score - prior.score
        direction = "improved" if delta > 0 else "worsened"
        trends.append(f"Operational health score {direction} by {abs(delta)} points since last assessment.")
        prior_ar = prior.components.get("ar_risk", 100)
        curr_ar = current.components.get("ar_risk", 100)
        if curr_ar < prior_ar - 5:
            trends.append(f"AR risk worsened ({prior_ar} → {curr_ar}).")
    for f in findings[:5]:
        if f.finding_type == "ar_aging_spike":
            trends.append("AR over 90 days increased relative to total receivables.")
        if f.finding_type == "inventory_adjustment_spike":
            trends.append("Inventory adjustments exceed historical baseline.")
    return trends
