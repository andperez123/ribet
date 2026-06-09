import { COMPONENT_LABELS } from "@/lib/dashboard/utils";
import type { AnalystOutput, HealthScore } from "@/lib/types/report";

export function HealthComponentsGrid({
  score,
  analystOutput,
}: {
  score: HealthScore;
  analystOutput?: AnalystOutput | null;
}) {
  const explanations = analystOutput?.dashboard_explanations;
  const entries = Object.entries(score.components || {}).filter(
    ([key]) => key !== "overall"
  );

  if (!entries.length) return null;

  const explanationFor = (key: string) => {
    if (!explanations) return null;
    const map: Record<string, string | undefined> = {
      ar_risk: explanations.ar_risk,
      cash_flow: explanations.cash_flow,
      inventory: explanations.inventory,
      data_quality: explanations.data_quality,
    };
    return map[key];
  };

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {entries.map(([key, value]) => (
        <div
          key={key}
          className="rounded-2xl border border-ribet-border bg-ribet-card p-6"
        >
          <p className="text-sm text-ribet-muted">
            {COMPONENT_LABELS[key] ?? key.replace(/_/g, " ")}
          </p>
          <p
            className={`mt-2 text-2xl font-semibold ${
              value < 60 ? "text-ribet-risk" : "text-ribet-text"
            }`}
          >
            {value}
          </p>
          {explanationFor(key) && (
            <p className="mt-3 text-xs leading-relaxed text-ribet-muted">
              {explanationFor(key)}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
