import { Card } from "@/components/ui/Card";
import { formatCurrency } from "@/lib/dashboard/utils";
import type { OrgCoverage } from "@/lib/types/coverage";
import type { OperationalSnapshotOut } from "@/lib/types/snapshot";

export function PartialDataHero({
  orgCoverage,
  snapshot,
}: {
  orgCoverage: OrgCoverage;
  snapshot?: OperationalSnapshotOut | null;
}) {
  const understood = orgCoverage.understood;

  const kpis: { label: string; value: string }[] = [];
  if (snapshot?.ar_total != null && snapshot.ar_total > 0) {
    kpis.push({ label: "Open AR", value: formatCurrency(snapshot.ar_total) });
  }
  if (snapshot?.ap_total != null && snapshot.ap_total > 0) {
    kpis.push({ label: "Open AP", value: formatCurrency(snapshot.ap_total) });
  }
  if (snapshot?.health_score != null) {
    kpis.push({
      label: "Last health score",
      value: String(snapshot.health_score),
    });
  }
  if (snapshot?.ar_over_90_pct != null && snapshot.ar_over_90_pct > 0) {
    kpis.push({
      label: "AR over 90d",
      value: `${snapshot.ar_over_90_pct.toFixed(0)}%`,
    });
  }

  return (
    <section className="space-y-4">
      <Card variant="hero" className="!bg-gradient-to-br from-ribet-ink to-ribet-ink-soft">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ribet-green/80">
          Partial picture · {orgCoverage.analysis_confidence}% confidence
        </p>
        <h2 className="mt-3 text-xl font-semibold leading-snug text-white md:text-2xl">
          Ribet understands{" "}
          {understood.map((u) => u.label).join(", ") || "some of your data"}.
          Generate a report to unlock the full business story.
        </h2>
      </Card>

      {kpis.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {kpis.map((kpi) => (
            <Card key={kpi.label} variant="stat">
              <p className="text-[10px] font-medium uppercase tracking-wide text-ribet-muted">
                {kpi.label}
              </p>
              <p className="mt-1 text-lg font-semibold tabular-nums text-ribet-text">
                {kpi.value}
              </p>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
