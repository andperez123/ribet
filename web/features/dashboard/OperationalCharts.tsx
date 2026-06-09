import { Card } from "@/components/ui/Card";
import { formatCurrency } from "@/lib/dashboard/utils";
import type { DataCoverage, DataDigest } from "@/lib/types/report";

function BarChart({
  title,
  caption,
  items,
}: {
  title: string;
  caption: string;
  items: { label: string; value: number; tone?: string }[];
}) {
  const max = Math.max(...items.map((i) => i.value), 1);
  return (
    <Card>
      <h3 className="text-sm font-semibold text-ribet-text">{title}</h3>
      <p className="mt-1 text-xs text-ribet-muted">{caption}</p>
      <div className="mt-4 space-y-3">
        {items.map((item) => (
          <div key={item.label}>
            <div className="mb-1 flex justify-between text-xs text-ribet-muted">
              <span>{item.label}</span>
              <span>{formatCurrency(item.value)}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-ribet-border/40">
              <div
                className={`h-full rounded-full ${item.tone ?? "bg-ribet-green/80"}`}
                style={{ width: `${Math.max(4, (item.value / max) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function OperationalCharts({
  digest,
  coverage,
}: {
  digest: DataDigest;
  coverage: DataCoverage;
}) {
  const apBuckets =
    coverage.ap &&
    (digest.ap_current > 0 ||
      digest.ap_1_30 > 0 ||
      digest.ap_31_60 > 0 ||
      digest.ap_61_90 > 0 ||
      digest.ap_91_plus > 0)
      ? [
          { label: "Current", value: digest.ap_current, tone: "bg-emerald-500/70" },
          { label: "1–30 days", value: digest.ap_1_30, tone: "bg-ribet-green/70" },
          { label: "31–60 days", value: digest.ap_31_60, tone: "bg-amber-500/70" },
          { label: "61–90 days", value: digest.ap_61_90, tone: "bg-orange-500/70" },
          { label: "91+ days", value: digest.ap_91_plus, tone: "bg-ribet-risk/70" },
        ].filter((b) => b.value > 0)
      : [];

  const topCustomers = coverage.ar
    ? digest.top_customers.slice(0, 5).map((c) => ({
        label: c.label,
        value: c.amount,
        tone: c.pct >= 25 ? "bg-ribet-risk/70" : "bg-ribet-green/70",
      }))
    : [];

  const latePos = coverage.purchase_orders
    ? digest.top_late_pos.slice(0, 5).map((p) => ({
        label: p.label,
        value: p.amount,
        tone: "bg-orange-500/70",
      }))
    : [];

  const pastDueSos = coverage.sales_orders
    ? digest.top_past_due_orders.slice(0, 5).map((s) => ({
        label: s.label,
        value: s.amount,
        tone: "bg-ribet-risk/70",
      }))
    : [];

  if (!apBuckets.length && !topCustomers.length && !latePos.length && !pastDueSos.length) {
    return null;
  }

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold text-ribet-text">Visual breakdown</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        {apBuckets.length > 0 && (
          <BarChart
            title="AP aging buckets"
            caption="Open payables by days outstanding (USD)"
            items={apBuckets}
          />
        )}
        {topCustomers.length > 0 && (
          <BarChart
            title="Customer concentration"
            caption="Top customers by open AR balance (USD)"
            items={topCustomers}
          />
        )}
        {latePos.length > 0 && (
          <BarChart
            title="Late purchase orders"
            caption="Open PO value by vendor (USD)"
            items={latePos}
          />
        )}
        {pastDueSos.length > 0 && (
          <BarChart
            title="Past-due sales orders"
            caption="Open SO value by customer (USD)"
            items={pastDueSos}
          />
        )}
      </div>
      {coverage.ar && digest.ar_total > 0 && (
        <p className="text-xs text-ribet-muted">
          AR over 90 days: {digest.ar_over_90_pct.toFixed(1)}% (
          {formatCurrency(digest.ar_over_90)} of {formatCurrency(digest.ar_total)})
        </p>
      )}
    </section>
  );
}
