import hashlib
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Customer, GlTransaction, InventoryItem, Invoice, Vendor


@dataclass
class RuleFinding:
    finding_type: str
    title: str
    detail: str
    severity: str
    confidence: float
    business_impact: str
    department: str
    category: str
    suggested_action: str

    @property
    def fingerprint(self) -> str:
        raw = f"{self.finding_type}:{self.title}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def to_dict(self) -> dict:
        return {
            "finding_type": self.finding_type,
            "title": self.title,
            "detail": self.detail,
            "severity": self.severity,
            "confidence": self.confidence,
            "business_impact": self.business_impact,
            "department": self.department,
            "category": self.category,
            "suggested_action": self.suggested_action,
            "fingerprint": self.fingerprint,
        }


def run_rules(db: Session, org_id: UUID) -> list[RuleFinding]:
    findings: list[RuleFinding] = []
    findings.extend(_check_ar_aging_spike(db, org_id))
    findings.extend(_check_duplicate_customers(db, org_id))
    findings.extend(_check_ap_negative(db, org_id))
    findings.extend(_check_vendor_concentration(db, org_id))
    findings.extend(_check_inventory_adjustments(db, org_id))
    findings.extend(_check_orphan_inventory(db, org_id))
    findings.extend(_check_missing_gl_mappings(db, org_id))
    findings.extend(_check_invalid_aging_buckets(db, org_id))
    findings.extend(_check_duplicate_vendors(db, org_id))
    return findings


def _check_ar_aging_spike(db: Session, org_id: UUID) -> list[RuleFinding]:
    over_90 = (
        db.query(func.sum(Invoice.amount))
        .filter(Invoice.org_id == org_id, Invoice.days_overdue >= 90)
        .scalar()
        or 0
    )
    total = (
        db.query(func.sum(Invoice.amount)).filter(Invoice.org_id == org_id).scalar() or 0
    )
    if total <= 0:
        return []
    pct = (over_90 / total) * 100
    if pct < 15:
        return []
    return [
        RuleFinding(
            finding_type="ar_aging_spike",
            title="AR over 90 days elevated",
            detail=f"Receivables over 90 days represent {pct:.1f}% of total AR (${over_90:,.0f}).",
            severity="high" if pct > 25 else "medium",
            confidence=0.95,
            business_impact="cash_flow",
            department="finance",
            category="financial",
            suggested_action="Review top overdue accounts and collection workflow.",
        )
    ]


def _check_duplicate_customers(db: Session, org_id: UUID) -> list[RuleFinding]:
    dupes = (
        db.query(Customer.customer_id, func.count(Customer.id))
        .filter(Customer.org_id == org_id)
        .group_by(Customer.customer_id)
        .having(func.count(Customer.id) > 1)
        .all()
    )
    if not dupes:
        return []
    return [
        RuleFinding(
            finding_type="duplicate_customer_ids",
            title="Duplicate customer IDs detected",
            detail=f"Found {len(dupes)} customer ID(s) appearing more than once in exports.",
            severity="medium",
            confidence=1.0,
            business_impact="compliance",
            department="finance",
            category="data_quality",
            suggested_action="Reconcile customer master data in your ERP.",
        )
    ]


def _check_ap_negative(db: Session, org_id: UUID) -> list[RuleFinding]:
    negatives = db.query(Vendor).filter(Vendor.org_id == org_id, Vendor.balance < 0).all()
    if not negatives:
        return []
    return [
        RuleFinding(
            finding_type="ap_negative_balance",
            title="AP negative balances found",
            detail=f"{len(negatives)} vendor(s) show negative AP balances.",
            severity="medium",
            confidence=1.0,
            business_impact="cash_flow",
            department="finance",
            category="financial",
            suggested_action="Verify vendor credits and payment applications.",
        )
    ]


def _check_vendor_concentration(db: Session, org_id: UUID) -> list[RuleFinding]:
    vendors = db.query(Vendor).filter(Vendor.org_id == org_id, Vendor.balance > 0).all()
    if len(vendors) < 3:
        return []
    total = sum(v.balance or 0 for v in vendors)
    if total <= 0:
        return []
    top = max(vendors, key=lambda v: v.balance or 0)
    pct = ((top.balance or 0) / total) * 100
    if pct < 40:
        return []
    return [
        RuleFinding(
            finding_type="vendor_concentration",
            title="Vendor concentration risk",
            detail=f"Top vendor represents {pct:.1f}% of open AP.",
            severity="medium",
            confidence=0.9,
            business_impact="cash_flow",
            department="purchasing",
            category="risk",
            suggested_action="Diversify vendor base and review payment terms.",
        )
    ]


def _check_inventory_adjustments(db: Session, org_id: UUID) -> list[RuleFinding]:
    adj_keywords = ["adjustment", "adj", "write-off", "writeoff", "shrinkage"]
    gl_rows = db.query(GlTransaction).filter(GlTransaction.org_id == org_id).all()
    adj_total = 0.0
    for row in gl_rows:
        name = (row.account_name or row.account_id or "").lower()
        if any(kw in name for kw in adj_keywords):
            adj_total += abs(row.amount)
    if adj_total < 5000:
        return []
    return [
        RuleFinding(
            finding_type="inventory_adjustment_spike",
            title="Inventory adjustments above baseline",
            detail=f"Inventory adjustment activity totals ${adj_total:,.0f} in current data.",
            severity="high",
            confidence=0.88,
            business_impact="margin",
            department="operations",
            category="operational",
            suggested_action="Require PO receiving validation before inventory adjustments.",
        )
    ]


def _check_orphan_inventory(db: Session, org_id: UUID) -> list[RuleFinding]:
    orphans = (
        db.query(InventoryItem)
        .filter(
            InventoryItem.org_id == org_id,
            (InventoryItem.gl_account == None) | (InventoryItem.gl_account == ""),  # noqa: E711
        )
        .count()
    )
    if orphans == 0:
        return []
    return [
        RuleFinding(
            finding_type="orphan_inventory",
            title="Orphan inventory items",
            detail=f"{orphans} inventory item(s) lack GL account mapping.",
            severity="medium",
            confidence=1.0,
            business_impact="inventory",
            department="operations",
            category="data_quality",
            suggested_action="Map inventory items to GL accounts in your ERP.",
        )
    ]


def _check_missing_gl_mappings(db: Session, org_id: UUID) -> list[RuleFinding]:
    missing = (
        db.query(GlTransaction)
        .filter(
            GlTransaction.org_id == org_id,
            (GlTransaction.account_id == None) | (GlTransaction.account_id == ""),  # noqa: E711
        )
        .count()
    )
    if missing == 0:
        return []
    return [
        RuleFinding(
            finding_type="missing_gl_mappings",
            title="Missing GL account mappings",
            detail=f"{missing} transaction(s) have no account ID.",
            severity="high",
            confidence=1.0,
            business_impact="compliance",
            department="finance",
            category="data_quality",
            suggested_action="Complete GL mapping for all journal entries.",
        )
    ]


def _check_invalid_aging_buckets(db: Session, org_id: UUID) -> list[RuleFinding]:
    valid = {"current", "1-30", "31-60", "61-90", "91-120", "90+", ">90", "over 90"}
    invalid = (
        db.query(Invoice)
        .filter(Invoice.org_id == org_id, Invoice.aging_bucket != None, Invoice.aging_bucket != "")  # noqa: E711
        .all()
    )
    bad = [i for i in invalid if i.aging_bucket.lower() not in valid and not any(v in i.aging_bucket.lower() for v in ["90", "120"])]
    if not bad:
        return []
    return [
        RuleFinding(
            finding_type="invalid_aging_buckets",
            title="Invalid AR aging buckets",
            detail=f"{len(bad)} invoice(s) use non-standard aging categories.",
            severity="low",
            confidence=0.85,
            business_impact="compliance",
            department="finance",
            category="data_quality",
            suggested_action="Standardize aging bucket definitions in AR reports.",
        )
    ]


def _check_duplicate_vendors(db: Session, org_id: UUID) -> list[RuleFinding]:
    vendors = db.query(Vendor).filter(Vendor.org_id == org_id).all()
    names: dict[str, list] = {}
    for v in vendors:
        key = (v.name or "").lower().strip()
        if key:
            names.setdefault(key, []).append(v.vendor_id)
    dupes = {k: v for k, v in names.items() if len(v) > 1}
    if not dupes:
        return []
    return [
        RuleFinding(
            finding_type="inconsistent_vendor_naming",
            title="Inconsistent vendor naming",
            detail=f"{len(dupes)} vendor name(s) appear with multiple IDs.",
            severity="medium",
            confidence=0.92,
            business_impact="cash_flow",
            department="purchasing",
            category="data_quality",
            suggested_action="Merge duplicate vendor records in AP master.",
        )
    ]
