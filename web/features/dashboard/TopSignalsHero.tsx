import { Card } from "@/components/ui/Card";
import { SourceTraceabilityChip } from "@/features/reports/SourceTraceabilityChip";
import {
  signalSeverityClass,
  signalSeverityPill,
} from "@/lib/dashboard/report-signals";
import type { TopSignal } from "@/lib/types/report";

function pillClass(pill: "High" | "Medium" | "Low"): string {
  if (pill === "High") return "bg-ribet-risk/15 text-ribet-risk border-ribet-risk/40";
  if (pill === "Medium") return "bg-amber-500/15 text-amber-700 border-amber-500/40";
  return "bg-ribet-card text-ribet-muted border-ribet-border";
}

export function TopSignalsHero({
  signals,
  evidenceAnchorHref,
}: {
  signals: TopSignal[];
  evidenceAnchorHref?: string;
}) {
  if (!signals.length) return null;

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-ribet-text">Top signals</h2>
          <p className="mt-1 text-sm text-ribet-muted">
            Highest-impact findings from this report, ranked by severity.
          </p>
        </div>
        {evidenceAnchorHref && (
          <a
            href={evidenceAnchorHref}
            className="text-sm font-medium text-ribet-green hover:underline"
          >
            View evidence
          </a>
        )}
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        {signals.map((signal, i) => {
          const pill = signalSeverityPill(signal.severity);
          return (
            <Card
              key={`${signal.kind}-${signal.title}-${i}`}
              className={`border-2 ${signalSeverityClass(signal.severity)} ${
                i === 0 ? "lg:col-span-3" : ""
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <span
                  className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${pillClass(pill)}`}
                >
                  {pill}
                </span>
              </div>
              <p
                className={`mt-3 font-semibold text-ribet-text ${
                  i === 0 ? "text-xl" : "text-base"
                }`}
              >
                {signal.title}
              </p>
              {(signal.why_it_matters || signal.body) && (
                <div className="mt-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
                    Why this matters
                  </p>
                  <p className="mt-1 text-sm leading-relaxed text-ribet-text">
                    {signal.why_it_matters ?? signal.body}
                  </p>
                </div>
              )}
              {signal.suggested_action && (
                <div className="mt-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
                    Recommended action
                  </p>
                  <p className="mt-1 text-sm font-medium text-ribet-green">
                    → {signal.suggested_action}
                  </p>
                </div>
              )}
              {signal.metric_label && signal.metric_value && (
                <p className="mt-3 text-sm text-ribet-text">
                  {signal.metric_label}:{" "}
                  <span className="font-semibold tabular-nums">
                    {signal.metric_value}
                  </span>
                </p>
              )}
              <SourceTraceabilityChip
                trace={signal.source_trace}
                sourceLabel={signal.source}
                findingId={signal.finding_id}
                metricKey={signal.metric_label ?? undefined}
                className="mt-4"
              />
            </Card>
          );
        })}
      </div>
    </section>
  );
}
