import { Card } from "@/components/ui/Card";
import { INSIGHT_SEVERITY_STYLES } from "@/lib/dashboard/utils";
import type { DomainInsight } from "@/lib/types/report";

function severityLabel(severity: DomainInsight["severity"]): string {
  if (severity === "alert") return "Needs attention";
  if (severity === "watch") return "Monitor";
  return "Insight";
}

export function InsightCardsGrid({ insights }: { insights: DomainInsight[] }) {
  if (!insights.length) return null;

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold text-ribet-text">Insights</h2>
      <div className="grid gap-4 md:grid-cols-2">
        {insights.map((insight, i) => (
          <Card
            key={`${insight.domain}-${insight.title}-${i}`}
            className={`border ${INSIGHT_SEVERITY_STYLES[insight.severity]}`}
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
                {insight.domain}
              </p>
              <span className="text-xs text-ribet-muted">
                {severityLabel(insight.severity)}
              </span>
            </div>
            <p className="mt-2 font-medium text-ribet-text">{insight.title}</p>
            <p className="mt-1 text-sm text-ribet-muted">{insight.body}</p>
            {insight.metric_label && insight.metric_value && (
              <p className="mt-3 text-xs text-ribet-muted">
                {insight.metric_label}:{" "}
                <span className="font-medium text-ribet-text">
                  {insight.metric_value}
                </span>
              </p>
            )}
          </Card>
        ))}
      </div>
    </section>
  );
}
