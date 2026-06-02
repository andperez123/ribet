from __future__ import annotations

"""Graph coverage model — what Ribet understands vs needs (Phase 1, no edge graph)."""

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import GlTransaction, IngestJob, InventoryItem, Invoice, Vendor

COVERAGE_SPECS: list[dict] = [
    {
        "key": "ar_aging",
        "label": "AR Aging",
        "sector": "financials",
        "report_type": "ar_aging",
        "uploadable": True,
    },
    {
        "key": "ap_aging",
        "label": "AP Aging",
        "sector": "financials",
        "report_type": "ap_aging",
        "uploadable": True,
    },
    {
        "key": "gl_detail",
        "label": "GL Detail",
        "sector": "financials",
        "report_type": "gl_detail",
        "uploadable": True,
    },
    {
        "key": "inventory",
        "label": "Inventory",
        "sector": "manufacturing",
        "report_type": "inventory",
        "uploadable": True,
    },
    {
        "key": "invoice_detail",
        "label": "Invoice Detail",
        "sector": "financials",
        "report_type": "invoice_detail",
        "uploadable": False,
    },
    {
        "key": "sales_orders",
        "label": "Open Sales Orders",
        "sector": "sales",
        "report_type": "sales_orders",
        "uploadable": False,
    },
    {
        "key": "purchase_orders",
        "label": "Purchase Orders",
        "sector": "orders",
        "report_type": "purchase_orders",
        "uploadable": False,
    },
    {
        "key": "work_orders",
        "label": "Work Orders / Labor Detail",
        "sector": "manufacturing",
        "report_type": "work_orders",
        "uploadable": False,
    },
]


@dataclass
class CoverageItem:
    key: str
    label: str
    sector: str
    covered: bool
    uploadable: bool


@dataclass
class GraphCoverage:
    items: list[CoverageItem] = field(default_factory=list)
    report_types: set[str] = field(default_factory=set)

    @property
    def understood(self) -> list[CoverageItem]:
        return [i for i in self.items if i.covered]

    @property
    def needed(self) -> list[CoverageItem]:
        return [i for i in self.items if not i.covered]

    def has(self, key: str) -> bool:
        for item in self.items:
            if item.key == key:
                return item.covered
        return False

    def has_report_type(self, report_type: str) -> bool:
        return report_type in self.report_types


def _report_types_from_jobs(db: Session, org_id: UUID) -> set[str]:
    rows = (
        db.query(IngestJob.report_type)
        .filter(
            IngestJob.org_id == org_id,
            IngestJob.status == "done",
            IngestJob.report_type.isnot(None),
        )
        .distinct()
        .all()
    )
    return {r[0] for r in rows if r[0] and r[0] != "unknown"}


def _entity_signals(db: Session, org_id: UUID) -> dict[str, bool]:
    return {
        "ar_aging": db.query(Invoice.id).filter(Invoice.org_id == org_id).first() is not None,
        "ap_aging": db.query(Vendor.id).filter(Vendor.org_id == org_id).first() is not None,
        "gl_detail": db.query(GlTransaction.id).filter(GlTransaction.org_id == org_id).first()
        is not None,
        "inventory": db.query(InventoryItem.id)
        .filter(InventoryItem.org_id == org_id)
        .first()
        is not None,
    }


def get_graph_coverage(db: Session, org_id: UUID) -> GraphCoverage:
    report_types = _report_types_from_jobs(db, org_id)
    entities = _entity_signals(db, org_id)

    items: list[CoverageItem] = []
    for spec in COVERAGE_SPECS:
        rt = spec["report_type"]
        covered = rt in report_types or entities.get(spec["key"], False)
        items.append(
            CoverageItem(
                key=spec["key"],
                label=spec["label"],
                sector=spec["sector"],
                covered=covered,
                uploadable=spec["uploadable"],
            )
        )

    return GraphCoverage(items=items, report_types=report_types)
