import { Card } from "@/components/ui/Card";
import type { OperationalSnapshotOut } from "@/lib/types/snapshot";

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

export function SnapshotKpiGrid({
  current,
  prior,
}: {
  current: OperationalSnapshotOut;
  prior?: OperationalSnapshotOut | null;
}) {
  const items = [
    {
      label: "AR over 90 days",
      value:
        current.ar_over_90_pct != null
          ? `${current.ar_over_90_pct.toFixed(1)}%`
          : "—",
      delta: fmtDelta(current.ar_over_90_pct, prior?.ar_over_90_pct ?? null, "%"),
    },
    {
      label: "Vendor concentration",
      value:
        current.vendor_concentration != null
          ? `${current.vendor_concentration.toFixed(1)}%`
          : "—",
      delta: fmtDelta(
        current.vendor_concentration,
        prior?.vendor_concentration ?? null,
        "%"
      ),
    },
    {
      label: "Inventory (qty sum)",
      value:
        current.inventory_value != null
          ? current.inventory_value.toLocaleString()
          : "—",
      delta: fmtDelta(current.inventory_value, prior?.inventory_value ?? null),
    },
    {
      label: "Period",
      value: current.period,
      delta: null,
    },
  ];

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
