import { Card } from "@/components/ui/Card";
import { formatCurrency } from "@/lib/dashboard/utils";
import type { DataCoverage, DataDigest } from "@/lib/types/report";

function EntityTable({
  title,
  rows,
}: {
  title: string;
  rows: { label: string; amount: number; pct: number; detail?: string }[];
}) {
  if (!rows.length) return null;
  return (
    <Card>
      <h3 className="text-sm font-semibold text-ribet-text">{title}</h3>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ribet-border text-left text-xs text-ribet-muted">
              <th className="pb-2 font-medium">Name</th>
              <th className="pb-2 font-medium">Amount</th>
              <th className="pb-2 font-medium">Share</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.label}
                className="border-b border-ribet-border/40 last:border-0"
              >
                <td className="py-2.5 text-ribet-text">
                  {row.label}
                  {row.detail && (
                    <span className="mt-0.5 block text-xs text-ribet-muted">
                      {row.detail}
                    </span>
                  )}
                </td>
                <td className="py-2.5 text-ribet-muted">
                  {formatCurrency(row.amount)}
                </td>
                <td className="py-2.5 text-ribet-muted">{row.pct.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

export function TopEntitiesPanel({
  digest,
  coverage,
}: {
  digest: DataDigest;
  coverage: DataCoverage;
}) {
  const customers = coverage.ar ? digest.top_customers : [];
  const vendors = coverage.ap ? digest.top_vendors : [];
  const latePos = coverage.purchase_orders ? digest.top_late_pos : [];
  const pastDueOrders = coverage.sales_orders ? digest.top_past_due_orders : [];
  if (!customers.length && !vendors.length && !latePos.length && !pastDueOrders.length) {
    return null;
  }

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold text-ribet-text">Top entities</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <EntityTable title="Top customers" rows={customers} />
        <EntityTable title="Top vendors" rows={vendors} />
        <EntityTable title="Late purchase orders" rows={latePos} />
        <EntityTable title="Past-due sales orders" rows={pastDueOrders} />
      </div>
    </section>
  );
}
