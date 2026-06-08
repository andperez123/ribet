import { Card } from "@/components/ui/Card";
import { signalSeverityClass } from "@/lib/dashboard/report-signals";
import type { TopSignal } from "@/lib/types/report";

function severityLabel(severity: string): string {
  const s = severity.toLowerCase();
  if (s === "critical" || s === "high" || s === "alert") return "Needs attention";
  if (s === "medium" || s === "watch") return "Monitor";
  return "Insight";
}

export function TopSignalsHero({ signals }: { signals: TopSignal[] }) {
  if (!signals.length) return null;

  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold text-ribet-text">Top signals</h2>
        <p className="mt-1 text-sm text-ribet-muted">
          The most important items from this report, ranked by severity.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        {signals.map((signal, i) => (
          <Card
            key={`${signal.kind}-${signal.title}-${i}`}
            className={`border-2 ${signalSeverityClass(signal.severity)} ${
              i === 0 ? "lg:col-span-3" : ""
            }`}
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
                Signal {i + 1}
              </p>
              <span className="text-xs text-ribet-muted">
                {severityLabel(signal.severity)}
              </span>
            </div>
            <p
              className={`mt-2 font-semibold text-ribet-text ${
                i === 0 ? "text-xl" : "text-base"
              }`}
            >
              {signal.title}
            </p>
            <p className="mt-2 text-sm leading-relaxed text-ribet-muted">
              {signal.body}
            </p>
            {signal.metric_label && signal.metric_value && (
              <p className="mt-3 text-sm text-ribet-text">
                {signal.metric_label}:{" "}
                <span className="font-semibold tabular-nums">
                  {signal.metric_value}
                </span>
              </p>
            )}
            {signal.suggested_action && (
              <p className="mt-3 text-sm font-medium text-ribet-green">
                → {signal.suggested_action}
              </p>
            )}
            {signal.source && (
              <p className="mt-3 text-xs text-ribet-muted">{signal.source}</p>
            )}
          </Card>
        ))}
      </div>
    </section>
  );
}
