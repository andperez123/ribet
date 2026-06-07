import { Card } from "@/components/ui/Card";
import type { OperationalSnapshotOut } from "@/lib/types/snapshot";
import { formatCurrency } from "@/lib/dashboard/utils";

function fmtDelta(
  current: number | null,
  prior: number | null,
  suffix = ""
): string | null {
  if (current == null || prior == null) return null;
  const d = current - prior;
  if (Math.abs(d) < 0.5) return null;
  const sign = d > 0 ? "+" : "";
  return `${sign}${d.toFixed(1)}${suffix} vs prior`;
}

type SnapshotCard = {
  label: string;
  value: string;
  delta: string | null;
};

function buildSnapshotCards(
  current: OperationalSnapshotOut,
  prior?: OperationalSnapshotOut | null
): SnapshotCard[] {
  const cards: SnapshotCard[] = [];

  if ((current.ar_total ?? 0) > 0) {
    cards.push({
      label: "AR over 90 days",
      value:
        current.ar_over_90_pct != null
          ? `${current.ar_over_90_pct.toFixed(1)}%`
          : "—",
      delta: fmtDelta(current.ar_over_90_pct, prior?.ar_over_90_pct ?? null, "%"),
    });
    cards.push({
      label: "Total receivables",
      value: formatCurrency(current.ar_total ?? 0),
      delta: fmtDelta(current.ar_total, prior?.ar_total ?? null),
    });
  }

  if ((current.ap_total ?? 0) > 0) {
    cards.push({
      label: "Open payables",
      value: formatCurrency(current.ap_total ?? 0),
      delta: fmtDelta(current.ap_total, prior?.ap_total ?? null),
    });
    if ((current.vendor_concentration ?? 0) > 0) {
      cards.push({
        label: "Vendor concentration",
        value: `${current.vendor_concentration!.toFixed(1)}%`,
        delta: fmtDelta(
          current.vendor_concentration,
          prior?.vendor_concentration ?? null,
          "%"
        ),
      });
    }
  }

  if ((current.inventory_value ?? 0) > 0) {
    cards.push({
      label: "Inventory (qty sum)",
      value: current.inventory_value!.toLocaleString(),
      delta: fmtDelta(current.inventory_value, prior?.inventory_value ?? null),
    });
  }

  cards.push({
    label: "Period",
    value: current.period,
    delta: null,
  });

  return cards.slice(0, 4);
}

export function SnapshotKpiGrid({
  current,
  prior,
}: {
  current: OperationalSnapshotOut;
  prior?: OperationalSnapshotOut | null;
}) {
  const items = buildSnapshotCards(current, prior);

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <p className="text-sm text-ribet-muted">{item.label}</p>
          <p className="mt-2 text-2xl font-semibold text-ribet-text">
            {item.value}
          </p>
          {item.delta && (
            <p className="mt-1 text-xs text-ribet-muted">{item.delta}</p>
          )}
        </Card>
      ))}
    </div>
  );
}
