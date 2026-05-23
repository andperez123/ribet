from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_organization, verify_api_key
from app.models import OperationalFinding, OperationalReport, Organization
from app.schemas import WeeklyBrief

router = APIRouter(prefix="/v1/brief", tags=["brief"])


@router.get("/weekly", response_model=WeeklyBrief)
def weekly_brief(
    org: Organization = Depends(get_organization),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
):
    report = (
        db.query(OperationalReport)
        .filter(OperationalReport.org_id == org.id)
        .order_by(OperationalReport.generated_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="No data for brief")

    findings = (
        db.query(OperationalFinding)
        .filter(OperationalFinding.org_id == org.id)
        .order_by(OperationalFinding.detected_at.desc())
        .limit(20)
        .all()
    )

    sections: dict[str, list[str]] = {
        "cash_position": [],
        "ap_aging": [],
        "labor_variance": [],
        "inventory_adjustments": [],
        "duplicate_invoices": [],
        "vendor_concentration": [],
    }

    for f in findings:
        if f.business_impact == "cash_flow" or f.finding_type == "ar_aging_spike":
            sections["cash_position"].append(f.title)
        if f.finding_type in ("ap_negative_balance", "inconsistent_vendor_naming"):
            sections["ap_aging"].append(f.title)
        if f.finding_type == "inventory_adjustment_spike":
            sections["inventory_adjustments"].append(f.title)
        if f.finding_type == "vendor_concentration":
            sections["vendor_concentration"].append(f.title)
        if "duplicate" in f.finding_type:
            sections["duplicate_invoices"].append(f.title)

    for key in sections:
        if not sections[key]:
            sections[key].append("No issues detected in this area.")

    if report.trend_snapshot:
        sections["summary"] = report.trend_snapshot[:3]

    return WeeklyBrief(org_id=org.id, period="weekly", sections=sections)
