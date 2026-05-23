import { COMPONENT_LABELS } from "@/lib/dashboard/utils";
import type { HealthScore } from "@/lib/types/report";

export function HealthComponentsGrid({ score }: { score: HealthScore }) {
  const entries = Object.entries(score.components || {}).filter(
    ([key]) => key !== "overall"
  );

  if (!entries.length) return null;

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
        </div>
      ))}
    </div>
  );
}
