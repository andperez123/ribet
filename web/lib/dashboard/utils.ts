import type { Severity } from "@/lib/types/report";

const SEVERITY_RANK: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

export function severityRank(severity: Severity | undefined): number {
  if (!severity) return 99;
  return SEVERITY_RANK[severity.toLowerCase()] ?? 50;
}

export function isHighSeverity(severity: Severity | undefined): boolean {
  const s = severity?.toLowerCase();
  return s === "high" || s === "critical";
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function healthStatusColor(status: string): string {
  const s = status.toLowerCase();
  if (s.includes("critical") || s.includes("risk")) return "text-rivet-risk";
  if (s.includes("stable") || s.includes("good")) return "text-rivet-green";
  return "text-rivet-text";
}

export const COMPONENT_LABELS: Record<string, string> = {
  cash_flow: "Cash flow",
  ar_risk: "AR risk",
  inventory: "Inventory",
  data_quality: "Data quality",
  overall: "Overall",
};

export const BRIEF_SECTION_LABELS: Record<string, string> = {
  cash_position: "Cash position",
  ap_aging: "AP aging",
  labor_variance: "Labor variance",
  inventory_adjustments: "Inventory adjustments",
  duplicate_invoices: "Duplicate invoices",
  vendor_concentration: "Vendor concentration",
  summary: "Summary",
};
