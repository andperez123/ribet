export type SectorId = "financials" | "manufacturing" | "orders" | "sales";

export type SectorDef = {
  id: SectorId;
  label: string;
  description: string;
  examples: string;
  comingSoon?: boolean;
};

export const SECTORS: SectorDef[] = [
  {
    id: "financials",
    label: "Financials",
    description: "AR/AP aging, GL detail, and cash-related exports.",
    examples: "AR aging, AP aging, GL detail",
  },
  {
    id: "manufacturing",
    label: "Manufacturing",
    description: "Inventory, work-in-progress, and shop-floor data.",
    examples: "Inventory on hand, adjustments",
  },
  {
    id: "orders",
    label: "Orders",
    description: "Purchase orders, vendor receipts, and procurement.",
    examples: "PO exports, vendor open orders",
    comingSoon: true,
  },
  {
    id: "sales",
    label: "Sales",
    description: "Sales orders, invoices, and customer revenue.",
    examples: "Sales orders, customer revenue",
    comingSoon: true,
  },
];

export const DEFAULT_SECTOR: SectorId = "financials";
