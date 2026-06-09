import { Card } from "@/components/ui/Card";
import type { AnalystOutput, TopRisk } from "@/lib/types/report";

export function TopRisksPanel({ analystOutput }: { analystOutput?: AnalystOutput | null }) {
  const risks = analystOutput?.top_risks ?? [];
  if (!risks.length) return null;

  return (
    <Card className="space-y-4">
      <h3 className="text-sm font-semibold text-ribet-text">Top business risks</h3>
      <ol className="space-y-4">
        {risks.map((risk: TopRisk) => (
          <li key={risk.rank} className="rounded-xl border border-ribet-border/60 p-4">
            <div className="flex items-start justify-between gap-3">
              <p className="font-medium text-ribet-text">
                #{risk.rank} {risk.title}
              </p>
              <span className="shrink-0 text-xs uppercase tracking-wide text-ribet-muted">
                {risk.impact} impact
              </span>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-ribet-text">{risk.narrative}</p>
            {risk.recommended_action && (
              <p className="mt-2 text-sm text-ribet-muted">{risk.recommended_action}</p>
            )}
            {risk.finding_ids?.length > 0 && (
              <p className="mt-2 font-mono text-xs text-ribet-muted">
                {risk.finding_ids.join(", ")}
              </p>
            )}
          </li>
        ))}
      </ol>
    </Card>
  );
}
