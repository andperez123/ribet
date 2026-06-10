import { AGING_COLORS, DonutChart, HBarChart, SegmentBar } from "@/components/charts";
import { Card } from "@/components/ui/Card";
import { formatCurrency } from "@/lib/dashboard/utils";
import type { AnalystOutput, DataCoverage, DataDigest } from "@/lib/types/report";

function DomainCard({
  title,
  insight,
  children,
}: {
  title: string;
  insight?: string | null;
  children: React.ReactNode;
}) {
  return (
    <Card className="flex flex-col">
      <h3 className="text-sm font-semibold text-ribet-text">{title}</h3>
      {insight && (
        <p className="mt-2 text-sm leading-relaxed text-ribet-muted">{insight}</p>
      )}
      <div className="mt-4 flex-1">{children}</div>
    </Card>
  );
}

function CashReceivablesModule({
  digest,
  insight,
}: {
  digest: DataDigest;
  insight?: string | null;
}) {
  const agingSlices = [
    { name: "Current", value: digest.ar_total - digest.ar_over_90 },
    { name: "Over 90d", value: digest.ar_over_90 },
  ].filter((s) => s.value > 0);

  const customers = digest.top_customers.slice(0, 5).map((c) => ({
    label: c.label,
    value: c.amount,
    risk: c.pct >= 25,
  }));

  return (
    <DomainCard title="Cash & receivables" insight={insight}>
      <div className="grid gap-4 md:grid-cols-2">
        {agingSlices.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-ribet-muted">AR aging</p>
            <DonutChart
              data={agingSlices.map((s, i) => ({
                ...s,
                color: AGING_COLORS[i % AGING_COLORS.length],
              }))}
              centerValue={formatCurrency(digest.ar_total)}
              centerLabel="Total AR"
            />
          </div>
        )}
        {customers.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-ribet-muted">
              Customer concentration
            </p>
            <HBarChart data={customers} />
          </div>
        )}
      </div>
      {digest.ar_over_90_pct > 0 && (
        <p className="mt-3 text-xs text-ribet-muted">
          {digest.ar_over_90_pct.toFixed(1)}% of AR is over 90 days (
          {formatCurrency(digest.ar_over_90)})
        </p>
      )}
    </DomainCard>
  );
}

function PayablesModule({
  digest,
  insight,
}: {
  digest: DataDigest;
  insight?: string | null;
}) {
  const buckets = [
    { key: "current", label: "Current", value: digest.ap_current },
    { key: "1_30", label: "1–30d", value: digest.ap_1_30 },
    { key: "31_60", label: "31–60d", value: digest.ap_31_60 },
    { key: "61_90", label: "61–90d", value: digest.ap_61_90 },
    { key: "91_plus", label: "91+d", value: digest.ap_91_plus },
  ].filter((b) => b.value > 0);

  const vendors = digest.top_vendors.slice(0, 5).map((v) => ({
    label: v.label,
    value: v.amount,
  }));

  return (
    <DomainCard title="Payables & cash flow" insight={insight}>
      {buckets.length > 0 && (
        <SegmentBar
          segments={buckets.map((b, i) => ({
            key: b.key,
            label: b.label,
            weight: b.value,
            covered: true,
            highlighted: i === buckets.length - 1,
          }))}
          showLabels
        />
      )}
      {vendors.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-medium text-ribet-muted">Top vendors</p>
          <HBarChart data={vendors} />
        </div>
      )}
      <p className="mt-3 text-xs text-ribet-muted">
        Total open AP: {formatCurrency(digest.ap_total)}
      </p>
    </DomainCard>
  );
}

function InventoryModule({
  digest,
  insight,
}: {
  digest: DataDigest;
  insight?: string | null;
}) {
  const qualitySegments = [
    {
      key: "ok",
      label: "Healthy",
      weight: Math.max(
        0,
        digest.inventory_item_count -
          digest.inventory_negative_count -
          digest.inventory_zero_count -
          digest.inventory_orphan_count
      ),
      covered: true,
    },
    {
      key: "neg",
      label: "Negative",
      weight: digest.inventory_negative_count,
      covered: digest.inventory_negative_count === 0,
    },
    {
      key: "zero",
      label: "Zero qty",
      weight: digest.inventory_zero_count,
      covered: digest.inventory_zero_count === 0,
    },
    {
      key: "orphan",
      label: "Orphan",
      weight: digest.inventory_orphan_count,
      covered: digest.inventory_orphan_count === 0,
    },
  ].filter((s) => s.weight > 0);

  return (
    <DomainCard title="Inventory health" insight={insight}>
      {qualitySegments.length > 0 && (
        <SegmentBar segments={qualitySegments} showLabels />
      )}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-ribet-bg px-3 py-2">
          <p className="text-[10px] uppercase text-ribet-muted">SKUs</p>
          <p className="text-lg font-semibold tabular-nums">
            {digest.inventory_item_count.toLocaleString()}
          </p>
        </div>
        <div className="rounded-lg bg-ribet-bg px-3 py-2">
          <p className="text-[10px] uppercase text-ribet-muted">Total qty</p>
          <p className="text-lg font-semibold tabular-nums">
            {digest.inventory_total_qty.toLocaleString()}
          </p>
        </div>
      </div>
    </DomainCard>
  );
}

function OrdersModule({ digest, coverage }: { digest: DataDigest; coverage: DataCoverage }) {
  const latePos = digest.top_late_pos.slice(0, 5).map((p) => ({
    label: p.label,
    value: p.amount,
  }));
  const pastDueSos = digest.top_past_due_orders.slice(0, 5).map((s) => ({
    label: s.label,
    value: s.amount,
    risk: true,
  }));

  if (!latePos.length && !pastDueSos.length) return null;

  return (
    <DomainCard title="Orders & fulfillment">
      <div className="grid gap-4 md:grid-cols-2">
        {coverage.purchase_orders && latePos.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-ribet-muted">Late POs</p>
            <HBarChart data={latePos} />
          </div>
        )}
        {coverage.sales_orders && pastDueSos.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-ribet-muted">Past-due SOs</p>
            <HBarChart data={pastDueSos} />
          </div>
        )}
      </div>
    </DomainCard>
  );
}

function DataQualityModule({
  digest,
  insight,
}: {
  digest: DataDigest;
  insight?: string | null;
}) {
  return (
    <DomainCard title="Data quality" insight={insight}>
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-lg bg-ribet-bg px-3 py-3 text-center">
          <p className="text-2xl font-semibold tabular-nums text-ribet-text">
            {digest.gl_txn_count.toLocaleString()}
          </p>
          <p className="mt-1 text-[10px] uppercase text-ribet-muted">GL txns</p>
        </div>
        <div className="rounded-lg bg-ribet-bg px-3 py-3 text-center">
          <p
            className={`text-2xl font-semibold tabular-nums ${
              digest.gl_unmapped_count > 0 ? "text-ribet-risk" : "text-ribet-text"
            }`}
          >
            {digest.gl_unmapped_count}
          </p>
          <p className="mt-1 text-[10px] uppercase text-ribet-muted">Unmapped</p>
        </div>
        <div className="rounded-lg bg-ribet-bg px-3 py-3 text-center">
          <p className="text-2xl font-semibold tabular-nums text-ribet-text">
            {formatCurrency(digest.gl_adjustment_total)}
          </p>
          <p className="mt-1 text-[10px] uppercase text-ribet-muted">Adjustments</p>
        </div>
      </div>
    </DomainCard>
  );
}

export function DomainStoryGrid({
  digest,
  coverage,
  analystOutput,
}: {
  digest: DataDigest;
  coverage: DataCoverage;
  analystOutput?: AnalystOutput | null;
}) {
  const explanations = analystOutput?.dashboard_explanations;
  const modules: React.ReactNode[] = [];

  if (coverage.ar) {
    modules.push(
      <CashReceivablesModule
        key="ar"
        digest={digest}
        insight={explanations?.ar_risk}
      />
    );
  }
  if (coverage.ap) {
    modules.push(
      <PayablesModule
        key="ap"
        digest={digest}
        insight={explanations?.cash_flow}
      />
    );
  }
  if (coverage.inventory) {
    modules.push(
      <InventoryModule
        key="inv"
        digest={digest}
        insight={explanations?.inventory}
      />
    );
  }
  const hasOrders =
    (coverage.purchase_orders && digest.top_late_pos.length > 0) ||
    (coverage.sales_orders && digest.top_past_due_orders.length > 0);
  if (hasOrders) {
    modules.push(
      <OrdersModule key="orders" digest={digest} coverage={coverage} />
    );
  }
  if (coverage.gl) {
    modules.push(
      <DataQualityModule
        key="gl"
        digest={digest}
        insight={explanations?.data_quality}
      />
    );
  }

  if (!modules.length) return null;

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ribet-text">By the numbers</h2>
        <p className="mt-1 text-sm text-ribet-muted">
          Domain breakdowns from your latest data.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">{modules}</div>
    </section>
  );
}
