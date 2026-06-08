import { Card } from "@/components/ui/Card";
import { SeverityBadge } from "@/features/dashboard/SeverityBadge";
import type { Finding } from "@/lib/types/report";

export function ReportFindingsList({ findings }: { findings: Finding[] }) {
  if (!findings.length) {
    return (
      <Card>
        <h2 className="text-sm font-semibold text-ribet-text">Findings</h2>
        <p className="mt-3 text-sm text-ribet-muted">
          No rule findings for this report. Review the insight cards above for
          what was analyzed.
        </p>
      </Card>
    );
  }

  return (
    <Card className="p-0">
      <div className="border-b border-ribet-border px-6 py-4">
        <h2 className="text-sm font-semibold text-ribet-text">Findings</h2>
        <p className="mt-1 text-xs text-ribet-muted">
          {findings.length} finding(s) for this report
        </p>
      </div>
      <ul className="divide-y divide-ribet-border/60">
        {findings.map((f) => (
          <li key={f.id} className="px-6 py-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <p className="font-medium text-ribet-text">{f.title}</p>
              <SeverityBadge severity={f.severity} />
            </div>
            <p className="mt-1 text-sm text-ribet-muted">
              {f.narrative || f.detail}
            </p>
            {(f.recommendation || f.suggested_action) && (
              <p className="mt-2 text-xs text-ribet-green">
                → {f.recommendation || f.suggested_action}
              </p>
            )}
            {f.gap_recommendation && (
              <p className="mt-2 rounded-lg border border-ribet-green/30 bg-ribet-green/5 px-3 py-2 text-xs text-ribet-text">
                {f.gap_recommendation}
              </p>
            )}
            <p className="mt-2 text-xs text-ribet-muted">
              {f.department} · {f.category}
            </p>
          </li>
        ))}
      </ul>
    </Card>
  );
}
