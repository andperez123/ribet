import { Card } from "@/components/ui/Card";
import type { OperationalReport } from "@/lib/types/report";

export function ReportSections({ report }: { report: OperationalReport }) {
  const hasTrends = report.trend_snapshot.length > 0;
  const hasActions = report.suggested_actions.length > 0;
  if (!hasTrends && !hasActions) return null;

  return (
    <div className="space-y-6">
      {hasActions && (
        <Card>
          <h3 className="text-sm font-semibold text-ribet-text">
            Suggested actions
          </h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ribet-muted">
            {report.suggested_actions.map((action, i) => (
              <li key={i}>{action}</li>
            ))}
          </ul>
        </Card>
      )}

      {hasTrends && (
        <Card>
          <h3 className="text-sm font-semibold text-ribet-text">Trends</h3>
          <ul className="mt-3 space-y-2 text-sm text-ribet-muted">
            {report.trend_snapshot.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
