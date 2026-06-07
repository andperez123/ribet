import { Card } from "@/components/ui/Card";
import { formatCurrency } from "@/lib/dashboard/utils";
import type { DataCoverage, DataDigest } from "@/lib/types/report";

type KpiItem = {
  label: string;
  value: string;
  sub?: string;
  variant?: "default" | "warning";
};

function buildKpis(digest: DataDigest, coverage: DataCoverage): KpiItem[] {
  const items: KpiItem[] = [];
  const primary = coverage.primary_domain;

  const apItems: KpiItem[] = [];
  if (coverage.ap) {
    apItems.push({
      label: "Open payables",
      value: formatCurrency(digest.ap_total),
      sub: `${digest.vendor_count} vendor record(s)`,
    });
    if (digest.top_vendors[0]) {
      apItems.push({
        label: "Top vendor share",
        value: `${digest.top_vendors[0].pct.toFixed(1)}%`,
        sub: digest.top_vendors[0].label,
      });
    }
    if (coverage.ap_aging_available) {
      if (digest.ap_31_60 > 0) {
        apItems.push({
          label: "AP 31–60 days",
          value: formatCurrency(digest.ap_31_60),
        });
      }
      if (digest.ap_91_plus > 0) {
        apItems.push({
          label: "AP 91+ days",
          value: formatCurrency(digest.ap_91_plus),
        });
      }
    }
  }

  const arItems: KpiItem[] = [];
  if (coverage.ar) {
    arItems.push({
      label: "Total receivables",
      value: formatCurrency(digest.ar_total),
      sub: `${digest.ar_invoice_count} invoice(s)`,
    });
    arItems.push({
      label: "AR over 90 days",
      value: `${digest.ar_over_90_pct.toFixed(1)}%`,
      sub: formatCurrency(digest.ar_over_90),
    });
  } else if (coverage.ar_unmapped) {
    arItems.push({
      label: "AR amounts not detected",
      value: `${digest.ar_invoice_count} row(s)`,
      sub: "Re-upload or confirm column mapping",
      variant: "warning",
    });
  }

  const otherItems: KpiItem[] = [];
  if (coverage.inventory) {
    otherItems.push({
      label: "Inventory items",
      value: digest.inventory_item_count.toLocaleString(),
      sub: `${digest.inventory_total_qty.toLocaleString()} total units`,
    });
  }
  if (coverage.gl) {
    otherItems.push({
      label: "GL transactions",
      value: digest.gl_txn_count.toLocaleString(),
      sub:
        digest.gl_adjustment_total > 0
          ? `${formatCurrency(digest.gl_adjustment_total)} adjustments`
          : undefined,
    });
  }

  if (primary === "ap") {
    items.push(...apItems, ...arItems, ...otherItems);
  } else if (primary === "ar") {
    items.push(...arItems, ...apItems, ...otherItems);
  } else {
    items.push(...arItems, ...apItems, ...otherItems);
  }

  return items;
}

export function DataDigestKpiGrid({
  digest,
  coverage,
}: {
  digest: DataDigest;
  coverage: DataCoverage;
}) {
  const items = buildKpis(digest, coverage);
  if (!items.length) return null;

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold text-ribet-text">Key metrics</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((item) => (
          <Card
            key={item.label}
            className={
              item.variant === "warning"
                ? "border-amber-500/40 bg-amber-500/5"
                : undefined
            }
          >
            <p className="text-sm text-ribet-muted">{item.label}</p>
            <p className="mt-2 text-2xl font-semibold text-ribet-text">
              {item.value}
            </p>
            {item.sub && (
              <p className="mt-1 text-xs text-ribet-muted">{item.sub}</p>
            )}
          </Card>
        ))}
      </div>
    </section>
  );
}
