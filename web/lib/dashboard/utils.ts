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
  if (s.includes("critical") || s.includes("risk")) return "text-ribet-risk";
  if (s.includes("stable") || s.includes("good")) return "text-ribet-green";
  return "text-ribet-text";
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

export const COVERAGE_DOMAIN_LABELS: Record<keyof import("@/lib/types/report").DataCoverage, string> = {
  ar: "Accounts receivable",
  ap: "Accounts payable",
  gl: "General ledger",
  inventory: "Inventory",
};

export function formatCoverageSummary(coverage: import("@/lib/types/report").DataCoverage): string {
  const analyzed: string[] = [];
  const missing: string[] = [];
  for (const [key, label] of Object.entries(COVERAGE_DOMAIN_LABELS)) {
    const covered = coverage[key as keyof typeof coverage];
    if (covered) analyzed.push(label);
    else missing.push(label);
  }
  if (!analyzed.length && missing.length) {
    return "No financial domains were detected in this upload. Upload AR, AP, GL, or inventory exports to generate insights.";
  }
  if (analyzed.length && !missing.length) {
    return `${analyzed.join(", ")} were analyzed for this report.`;
  }
  if (analyzed.length && missing.length) {
    return `${analyzed.join(" and ")} were analyzed. ${missing.join(", ")} were not included in this upload.`;
  }
  return "";
}

export const INSIGHT_SEVERITY_STYLES: Record<
  import("@/lib/types/report").InsightSeverity,
  string
> = {
  info: "border-ribet-border bg-ribet-card",
  watch: "border-amber-500/40 bg-amber-500/5",
  alert: "border-ribet-risk/50 bg-ribet-risk/5",
};

export function digestHasData(digest: import("@/lib/types/report").DataDigest | undefined): boolean {
  if (!digest) return false;
  return (
    digest.ar_total > 0 ||
    digest.ar_invoice_count > 0 ||
    digest.ap_total > 0 ||
    digest.vendor_count > 0 ||
    digest.gl_txn_count > 0 ||
    digest.inventory_item_count > 0
  );
}

export function formatCurrency(n: number): string {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}
