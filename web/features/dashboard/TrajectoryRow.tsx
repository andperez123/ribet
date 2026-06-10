import { AreaTrend } from "@/components/charts";
import { HBarChart } from "@/components/charts";
import { Card } from "@/components/ui/Card";
import { BRIEF_SECTION_LABELS, COMPONENT_LABELS } from "@/lib/dashboard/utils";
import type { HealthHistory, HealthScore, WeeklyBrief } from "@/lib/types/report";

function HealthComponentsChart({ score }: { score: HealthScore }) {
  const entries = Object.entries(score.components || {}).filter(
    ([key]) => key !== "overall"
  );
  if (!entries.length) return null;

  const data = entries.map(([key, value]) => ({
    label: COMPONENT_LABELS[key] ?? key.replace(/_/g, " "),
    value,
    risk: value < 60,
  }));

  return (
    <Card>
      <p className="text-sm font-semibold text-ribet-text">Health components</p>
      <p className="mt-1 text-xs text-ribet-muted">
        Score breakdown by operational area
      </p>
      <div className="mt-4">
        <HBarChart data={data} />
      </div>
    </Card>
  );
}

function CompactWeeklyBrief({ brief }: { brief: WeeklyBrief }) {
  const entries = Object.entries(brief.sections).filter(
    ([, items]) => items.length > 0
  );
  if (!entries.length) return null;

  const topSections = entries.slice(0, 3);

  return (
    <Card>
      <p className="text-sm font-semibold text-ribet-text">This week</p>
      <p className="mt-1 text-xs capitalize text-ribet-muted">{brief.period}</p>
      <div className="mt-4 space-y-4">
        {topSections.map(([key, items]) => (
          <div key={key}>
            <p className="text-[10px] font-medium uppercase tracking-wide text-ribet-muted">
              {BRIEF_SECTION_LABELS[key] ?? key.replace(/_/g, " ")}
            </p>
            <ul className="mt-1.5 space-y-1">
              {items.slice(0, 2).map((item, i) => (
                <li key={i} className="text-sm text-ribet-text">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function TrajectoryRow({
  healthHistory,
  healthScore,
  weeklyBrief,
}: {
  healthHistory?: HealthHistory | null;
  healthScore?: HealthScore | null;
  weeklyBrief?: WeeklyBrief | null;
}) {
  const snapshots = healthHistory?.snapshots ?? [];
  const trendData =
    snapshots.length > 1
      ? [...snapshots].reverse().map((s, i) => ({
          label: String(i),
          value: s.score,
          status: s.status,
        }))
      : [];

  if (!trendData.length && !healthScore && !weeklyBrief) return null;

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ribet-text">Trajectory</h2>
        <p className="mt-1 text-sm text-ribet-muted">
          How operational health is moving over time.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        {trendData.length > 1 && (
          <Card className="lg:col-span-2">
            <p className="text-sm font-semibold text-ribet-text">Health trend</p>
            <p className="mt-1 text-xs text-ribet-muted">
              Last {trendData.length} snapshots
            </p>
            <div className="mt-4">
              <AreaTrend data={trendData} height={140} />
            </div>
          </Card>
        )}
        {healthScore && <HealthComponentsChart score={healthScore} />}
        {weeklyBrief && <CompactWeeklyBrief brief={weeklyBrief} />}
      </div>
    </section>
  );
}
