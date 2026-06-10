import { RadialGauge, Sparkline } from "@/components/charts";
import { Card } from "@/components/ui/Card";
import { formatCurrency } from "@/lib/dashboard/utils";
import type { OrgCoverage } from "@/lib/types/coverage";
import type {
  AnalystOutput,
  ConfidenceScore,
  DataCoverage,
  DataDigest,
  OperationalReport,
} from "@/lib/types/report";

type KpiTile = {
  key: string;
  label: string;
  value: string;
  sub?: string;
  spark?: number[];
};

function buildKpiTiles(
  digest: DataDigest,
  coverage: DataCoverage
): KpiTile[] {
  const tiles: KpiTile[] = [];

  if (coverage.ar && digest.ar_total > 0) {
    tiles.push({
      key: "ar",
      label: "Open AR",
      value: formatCurrency(digest.ar_total),
      sub:
        digest.ar_over_90_pct > 0
          ? `${digest.ar_over_90_pct.toFixed(0)}% over 90d`
          : undefined,
    });
  }
  if (coverage.ap && digest.ap_total > 0) {
    tiles.push({
      key: "ap",
      label: "Open AP",
      value: formatCurrency(digest.ap_total),
      sub:
        digest.ap_over_60_pct > 0
          ? `${digest.ap_over_60_pct.toFixed(0)}% over 60d`
          : undefined,
    });
  }
  if (coverage.inventory && digest.inventory_item_count > 0) {
    tiles.push({
      key: "inv",
      label: "Inventory SKUs",
      value: digest.inventory_item_count.toLocaleString(),
      sub:
        digest.inventory_negative_count > 0
          ? `${digest.inventory_negative_count} negative`
          : undefined,
    });
  }
  if (coverage.gl && digest.gl_txn_count > 0) {
    tiles.push({
      key: "gl",
      label: "GL transactions",
      value: digest.gl_txn_count.toLocaleString(),
      sub:
        digest.gl_unmapped_count > 0
          ? `${digest.gl_unmapped_count} unmapped`
          : undefined,
    });
  }
  if (coverage.purchase_orders && digest.po_open_total > 0) {
    tiles.push({
      key: "po",
      label: "Open POs",
      value: formatCurrency(digest.po_open_total),
      sub:
        digest.po_late_count > 0
          ? `${digest.po_late_count} late`
          : undefined,
    });
  }
  if (coverage.sales_orders && digest.so_open_total > 0) {
    tiles.push({
      key: "so",
      label: "Open SOs",
      value: formatCurrency(digest.so_open_total),
      sub:
        digest.so_past_due_count > 0
          ? `${digest.so_past_due_count} past due`
          : undefined,
    });
  }

  return tiles.slice(0, 6);
}

function headlineFromReport(
  report: OperationalReport,
  analyst?: AnalystOutput | null
): string {
  const exec =
    analyst?.executive_summary?.[0] ??
    report.executive_summary?.[0] ??
    report.analyst_summary;
  if (exec) return exec;
  return `Operational health is ${report.health_status.toLowerCase()} at ${report.health_score}/100.`;
}

export function StoryHero({
  report,
  digest,
  coverage,
  orgCoverage,
  analystOutput,
  confidenceScore,
  healthSparkline,
  compact = false,
}: {
  report: OperationalReport;
  digest: DataDigest;
  coverage: DataCoverage;
  orgCoverage?: OrgCoverage | null;
  analystOutput?: AnalystOutput | null;
  confidenceScore?: ConfidenceScore | null;
  healthSparkline?: number[];
  compact?: boolean;
}) {
  const headline = headlineFromReport(report, analystOutput);
  const confidence =
    confidenceScore?.after ??
    orgCoverage?.analysis_confidence ??
    null;
  const delta = confidenceScore?.delta;
  const kpis = buildKpiTiles(digest, coverage);
  const period = report.period_label ?? "Current period";

  if (compact) {
    return (
      <Card variant="hero" className="space-y-4">
        <div className="flex flex-wrap items-center gap-6">
          <RadialGauge
            value={report.health_score}
            label="Health"
            sublabel={report.health_status}
            size={100}
          />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium uppercase tracking-widest text-white/50">
              {period}
            </p>
            <p className="mt-2 text-lg font-medium leading-snug text-white/95">
              {headline}
            </p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <section className="space-y-4">
      <Card variant="hero">
        <div className="grid gap-8 lg:grid-cols-[auto_1fr_auto] lg:items-center">
          <div className="flex flex-col items-center lg:items-start">
            <RadialGauge
              value={report.health_score}
              label="Health"
              sublabel={report.health_status}
              size={148}
            />
            <p className="mt-3 text-xs uppercase tracking-widest text-white/45">
              {period}
            </p>
          </div>

          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ribet-green/90">
              Business story
            </p>
            <h2 className="mt-3 text-2xl font-semibold leading-tight tracking-tight text-white md:text-3xl">
              {headline}
            </h2>
            {analystOutput?.executive_summary &&
              analystOutput.executive_summary.length > 1 && (
                <p className="mt-4 max-w-2xl text-sm leading-relaxed text-white/70">
                  {analystOutput.executive_summary.slice(1).join(" ")}
                </p>
              )}
          </div>

          {confidence !== null && (
            <div className="flex flex-col items-center">
              <RadialGauge
                value={confidence}
                label="Confidence"
                size={108}
              />
              {delta !== undefined && delta !== 0 && (
                <span
                  className={`mt-2 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    delta > 0
                      ? "bg-ribet-green/20 text-ribet-green"
                      : "bg-white/10 text-white/70"
                  }`}
                >
                  {delta > 0 ? "+" : ""}
                  {delta}% from last upload
                </span>
              )}
            </div>
          )}
        </div>
      </Card>

      {kpis.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          {kpis.map((kpi) => (
            <Card key={kpi.key} variant="stat">
              <p className="text-[10px] font-medium uppercase tracking-wide text-ribet-muted">
                {kpi.label}
              </p>
              <p className="mt-1 text-lg font-semibold tabular-nums text-ribet-text">
                {kpi.value}
              </p>
              {kpi.sub && (
                <p className="mt-0.5 text-xs text-ribet-muted">{kpi.sub}</p>
              )}
              {healthSparkline && healthSparkline.length > 1 && (
                <div className="mt-2 opacity-60">
                  <Sparkline data={healthSparkline} />
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
