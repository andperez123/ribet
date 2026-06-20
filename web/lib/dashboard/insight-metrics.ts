import { formatCurrency, formatCurrencyCompact } from "@/lib/dashboard/utils";
import type { DataCoverage, DataDigest } from "@/lib/types/report";

/** Shared vocabulary with api/app/services/ai_analyst/prompts.py METRIC_KEY_VOCABULARY */
export const METRIC_KEYS = [
  "receivables_vs_payables",
  "collections_at_risk",
  "customer_concentration",
  "payables_over_60",
  "vendor_concentration",
  "inventory_readiness",
  "gl_activity",
] as const;

export type MetricKey = (typeof METRIC_KEYS)[number];

export type InsightTone = "good" | "neutral" | "watch" | "alert";

export type InsightMetric = {
  key: MetricKey;
  label: string;
  value: string;
  context?: string;
  tone: InsightTone;
  hint?: string;
};

export type CustomerDataProfile = {
  domains: {
    ar: boolean;
    ap: boolean;
    gl: boolean;
    inventory: boolean;
    orders: boolean;
    sales: boolean;
  };
  maturity: "thin" | "usable" | "rich";
};

export type InsightMetricDefinition = {
  key: MetricKey;
  label: string;
  requiredDomains: (keyof CustomerDataProfile["domains"])[];
  priority: number;
  build: (digest: DataDigest, profile: CustomerDataProfile) => InsightMetric | null;
};

const TONE_RANK: Record<InsightTone, number> = {
  alert: 0,
  watch: 1,
  good: 2,
  neutral: 3,
};

function domainsCovered(
  profile: CustomerDataProfile,
  required: (keyof CustomerDataProfile["domains"])[]
): boolean {
  return required.every((d) => profile.domains[d] === true);
}

function apOver60Amount(digest: DataDigest): number {
  return digest.ap_61_90 + digest.ap_91_plus;
}

export function buildCustomerDataProfile(
  _digest: DataDigest,
  coverage: DataCoverage
): CustomerDataProfile {
  const domains = {
    ar: Boolean(coverage.ar),
    ap: Boolean(coverage.ap),
    gl: Boolean(coverage.gl),
    inventory: Boolean(coverage.inventory),
    orders: Boolean(coverage.purchase_orders),
    sales: Boolean(coverage.sales_orders),
  };
  const count = [domains.ar, domains.ap, domains.gl, domains.inventory].filter(
    Boolean
  ).length;
  const maturity =
    count <= 1 ? "thin" : count <= 3 ? ("usable" as const) : ("rich" as const);
  return { domains, maturity };
}

const metricCatalog: InsightMetricDefinition[] = [
  {
    key: "collections_at_risk",
    label: "Collections at risk",
    requiredDomains: ["ar"],
    priority: 95,
    build(digest) {
      if (!digest.ar_total || digest.ar_total <= 0) return null;
      const tone: InsightTone =
        digest.ar_over_90_pct > 20
          ? "alert"
          : digest.ar_over_90_pct > 10
            ? "watch"
            : "neutral";
      return {
        key: "collections_at_risk",
        label: "Collections at risk",
        value: `${digest.ar_over_90_pct.toFixed(1)}%`,
        context: `${formatCurrencyCompact(digest.ar_over_90)} over 90 days`,
        tone,
        hint: "Cash that may need follow-up",
      };
    },
  },
  {
    key: "payables_over_60",
    label: "Payables over 60 days",
    requiredDomains: ["ap"],
    priority: 92,
    build(digest) {
      if (!digest.ap_total || digest.ap_total <= 0) return null;
      const tone: InsightTone =
        digest.ap_over_60_pct > 30
          ? "alert"
          : digest.ap_over_60_pct > 15
            ? "watch"
            : "neutral";
      return {
        key: "payables_over_60",
        label: "Payables over 60 days",
        value: `${digest.ap_over_60_pct.toFixed(1)}%`,
        context: `${formatCurrencyCompact(apOver60Amount(digest))} over 60 days`,
        tone,
        hint: "Aging payables may affect cash planning",
      };
    },
  },
  {
    key: "receivables_vs_payables",
    label: "Receivables vs payables",
    requiredDomains: ["ar", "ap"],
    priority: 90,
    build(digest) {
      if (!digest.ar_total && !digest.ap_total) return null;
      const gap = digest.ar_total - digest.ap_total;
      const tone: InsightTone =
        digest.ap_total > digest.ar_total * 1.5 ? "watch" : "good";
      return {
        key: "receivables_vs_payables",
        label: "Receivables vs payables",
        value: formatCurrencyCompact(gap),
        context: `AR ${formatCurrencyCompact(digest.ar_total)} vs AP ${formatCurrencyCompact(digest.ap_total)}`,
        tone,
        hint: "Working capital position from open AR and AP",
      };
    },
  },
  {
    key: "inventory_readiness",
    label: "Inventory readiness",
    requiredDomains: ["inventory"],
    priority: 85,
    build(digest) {
      if (!digest.inventory_item_count || digest.inventory_item_count <= 0) {
        return null;
      }
      const unmappedPct =
        (digest.inventory_orphan_count / digest.inventory_item_count) * 100;
      const tone: InsightTone =
        unmappedPct > 50 ? "alert" : unmappedPct > 10 ? "watch" : "neutral";
      return {
        key: "inventory_readiness",
        label: "Inventory readiness",
        value: `${unmappedPct.toFixed(1)}% unmapped`,
        context: `${digest.inventory_item_count.toLocaleString()} SKUs · ${digest.inventory_zero_count.toLocaleString()} at zero`,
        tone,
        hint: "Items without GL mapping limit financial visibility",
      };
    },
  },
  {
    key: "customer_concentration",
    label: "Customer concentration",
    requiredDomains: ["ar"],
    priority: 80,
    build(digest) {
      const top = digest.top_customers[0];
      if (!top || !digest.ar_total) return null;
      const tone: InsightTone =
        top.pct > 40 ? "alert" : top.pct > 25 ? "watch" : "neutral";
      return {
        key: "customer_concentration",
        label: "Customer concentration",
        value: `${top.pct.toFixed(1)}%`,
        context: top.label,
        tone,
        hint: "Share of total receivables from your largest customer",
      };
    },
  },
  {
    key: "vendor_concentration",
    label: "Vendor concentration",
    requiredDomains: ["ap"],
    priority: 78,
    build(digest) {
      const top = digest.top_vendors[0];
      if (!top || !digest.ap_total) return null;
      const tone: InsightTone =
        top.pct > 40 ? "alert" : top.pct > 25 ? "watch" : "neutral";
      return {
        key: "vendor_concentration",
        label: "Vendor concentration",
        value: `${top.pct.toFixed(1)}%`,
        context: top.label,
        tone,
        hint: "Share of open payables with your largest vendor",
      };
    },
  },
  {
    key: "gl_activity",
    label: "GL activity",
    requiredDomains: ["gl"],
    priority: 40,
    build(digest, profile) {
      if (profile.maturity !== "thin") return null;
      if (!digest.gl_txn_count) return null;
      return {
        key: "gl_activity",
        label: "GL activity",
        value: digest.gl_txn_count.toLocaleString(),
        context:
          digest.gl_adjustment_total > 0
            ? `${formatCurrencyCompact(digest.gl_adjustment_total)} adjustments`
            : digest.gl_unmapped_count > 0
              ? `${digest.gl_unmapped_count} unmapped`
              : undefined,
        tone: digest.gl_unmapped_count > 0 ? "watch" : "neutral",
        hint: "Upload AR, AP, and inventory to unlock cross-domain insights",
      };
    },
  },
];

function sortMetrics(a: InsightMetric, b: InsightMetric, catalog: InsightMetricDefinition[]) {
  const toneDiff = TONE_RANK[a.tone] - TONE_RANK[b.tone];
  if (toneDiff !== 0) return toneDiff;
  const prioA = catalog.find((c) => c.key === a.key)?.priority ?? 0;
  const prioB = catalog.find((c) => c.key === b.key)?.priority ?? 0;
  if (prioB !== prioA) return prioB - prioA;
  return a.key.localeCompare(b.key);
}

export function selectInsightMetrics(
  digest: DataDigest,
  coverage: DataCoverage
): InsightMetric[] {
  const profile = buildCustomerDataProfile(digest, coverage);
  const metrics = metricCatalog
    .filter((def) => domainsCovered(profile, def.requiredDomains))
    .map((def) => def.build(digest, profile))
    .filter((m): m is InsightMetric => m !== null);

  const risk = metrics
    .filter((m) => m.tone === "alert" || m.tone === "watch")
    .sort((a, b) => sortMetrics(a, b, metricCatalog));
  const summary = metrics
    .filter((m) => m.tone === "good" || m.tone === "neutral")
    .sort((a, b) => sortMetrics(a, b, metricCatalog));

  return [...risk, ...summary].slice(0, 6);
}
