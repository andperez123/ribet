from __future__ import annotations

"""Business sectors, capability unlock rules, and report-type hints."""

from typing import Literal

Sector = Literal["financials", "manufacturing", "orders", "sales"]

SECTORS: tuple[str, ...] = ("financials", "manufacturing", "orders", "sales")

ACTIVE_SECTORS: tuple[str, ...] = ("financials", "manufacturing", "orders", "sales")

COMING_SOON_SECTORS: tuple[str, ...] = ()

REPORT_TYPE_TO_SECTOR: dict[str, str] = {
    "ar_aging": "financials",
    "ap_aging": "financials",
    "gl_detail": "financials",
    "inventory": "manufacturing",
    "purchase_orders": "orders",
    "sales_orders": "sales",
}

SECTOR_LABELS: dict[str, str] = {
    "financials": "Financials",
    "manufacturing": "Manufacturing",
    "orders": "Orders",
    "sales": "Sales",
}

CAPABILITIES: list[dict[str, str | list[str]]] = [
    {
        "id": "cash_flow_logistics",
        "name": "Cash flow logistics",
        "description": "AR/AP aging and GL insights for cash positioning.",
        "requires_sectors": ["financials"],
    },
    {
        "id": "inventory_logistics",
        "name": "Inventory logistics",
        "description": "Stock levels, adjustments, and shop-floor inventory signals.",
        "requires_sectors": ["manufacturing"],
    },
    {
        "id": "order_flow_logistics",
        "name": "Order & procurement flow",
        "description": "Purchase orders and vendor fulfillment patterns.",
        "requires_sectors": ["orders"],
    },
    {
        "id": "sales_logistics",
        "name": "Sales & customer logistics",
        "description": "Revenue trends and customer concentration.",
        "requires_sectors": ["sales"],
    },
    {
        "id": "cross_sector_insights",
        "name": "Cross-sector insights",
        "description": "Signals that span multiple areas of your operation.",
        "requires_min_sectors": 3,
    },
    {
        "id": "full_operational_map",
        "name": "Full operational map",
        "description": "Complete view across financials, manufacturing, orders, and sales.",
        "requires_min_sectors": 4,
    },
]


def validate_sector(sector: str | None) -> str | None:
    if sector is None or sector == "":
        return None
    if sector not in SECTORS:
        raise ValueError(f"Invalid sector: {sector}. Must be one of: {', '.join(SECTORS)}")
    if sector in COMING_SOON_SECTORS:
        raise ValueError(
            f"Sector '{sector}' is not enabled yet (coming soon). "
            f"Active sectors: {', '.join(ACTIVE_SECTORS)}"
        )
    return sector


def sector_from_report_type(report_type: str | None) -> str | None:
    if not report_type:
        return None
    return REPORT_TYPE_TO_SECTOR.get(report_type)


def evaluate_capabilities(covered_sectors: set[str]) -> list[str]:
    unlocked: list[str] = []
    for cap in CAPABILITIES:
        cap_id = str(cap["id"])
        required = cap.get("requires_sectors")
        if required:
            if all(s in covered_sectors for s in required):  # type: ignore[union-attr]
                unlocked.append(cap_id)
        elif cap.get("requires_min_sectors") is not None:
            min_n = int(cap["requires_min_sectors"])  # type: ignore[arg-type]
            if len(covered_sectors) >= min_n:
                unlocked.append(cap_id)
    return unlocked


def capability_requirement_text(cap: dict) -> str:
    required = cap.get("requires_sectors")
    if required:
        labels = [SECTOR_LABELS.get(s, s) for s in required]  # type: ignore[union-attr]
        return f"Upload {labels[0]} data to unlock"
    min_n = cap.get("requires_min_sectors")
    if min_n == 4:
        return "Upload data for all four sectors to unlock"
    if min_n == 3:
        return "Cover at least 3 sectors to unlock"
    return "Upload data to unlock"
