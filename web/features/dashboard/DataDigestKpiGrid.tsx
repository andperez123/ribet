import { Card } from "@/components/ui/Card";
import { formatCurrency } from "@/lib/dashboard/utils";
import type { DataCoverage, DataDigest } from "@/lib/types/report";

type KpiItem = {
  label: string;
  value: string;
  sub?: string;
};

function buildKpis(digest: DataDigest, coverage: DataCoverage): KpiItem[] {
  const items: KpiItem[] = [];

  if (coverage.ar) {
    items.push({
      label: "Total receivables",
      value: formatCurrency(digest.ar_total),
      sub: `${digest.ar_invoice_count} invoice(s)`,
    });
    items.push({
      label: "AR over 90 days",
      value: `${digest.ar_over_90_pct.toFixed(1)}%`,
      sub: formatCurrency(digest.ar_over_90),
    });
  }

  if (coverage.ap) {
    items.push({
      label: "Open payables",
      value: formatCurrency(digest.ap_total),
      sub: `${digest.vendor_count} vendor record(s)`,
    });
    if (digest.top_vendors[0]) {
      items.push({
        label: "Top vendor share",
        value: `${digest.top_vendors[0].pct.toFixed(1)}%`,
        sub: digest.top_vendors[0].label,
      });
    }
  }

  if (coverage.inventory) {
    items.push({
      label: "Inventory items",
      value: digest.inventory_item_count.toLocaleString(),
      sub: `${digest.inventory_total_qty.toLocaleString()} total units`,
    });
  }

  if (coverage.gl) {
    items.push({
      label: "GL transactions",
      value: digest.gl_txn_count.toLocaleString(),
      sub:
        digest.gl_adjustment_total > 0
          ? `${formatCurrency(digest.gl_adjustment_total)} adjustments`
          : undefined,
    });
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
          <Card key={item.label}>
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
