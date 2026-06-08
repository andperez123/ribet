import { Card } from "@/components/ui/Card";
import { SeverityBadge } from "@/features/dashboard/SeverityBadge";
import type { ActionItem, Finding } from "@/lib/types/report";

export function ReportActionItems({
  actionItems,
  findings,
}: {
  actionItems?: ActionItem[];
  findings: Finding[];
}) {
  const items: ActionItem[] =
    actionItems ??
    findings.map((f) => ({
      title: f.title,
      detail: f.narrative || f.detail,
      severity: f.severity ?? "medium",
      suggested_action: f.recommendation || f.suggested_action || undefined,
      gap_recommendation: undefined,
      finding_type: f.finding_type,
    }));

  if (!items.length) {
    return (
      <Card>
        <h2 className="text-sm font-semibold text-ribet-text">Action items</h2>
        <p className="mt-3 text-sm text-ribet-muted">
          No rule findings for this report. Review the top signals and insight
          cards for what was analyzed.
        </p>
      </Card>
    );
  }

  return (
    <Card className="p-0">
      <div className="border-b border-ribet-border px-6 py-4">
        <h2 className="text-sm font-semibold text-ribet-text">Action items</h2>
        <p className="mt-1 text-xs text-ribet-muted">
          {items.length} item(s) requiring attention
        </p>
      </div>
      <ul className="divide-y divide-ribet-border/60">
        {items.map((item, i) => (
          <li key={`${item.finding_type ?? "item"}-${item.title}-${i}`} className="px-6 py-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <p className="font-medium text-ribet-text">{item.title}</p>
              <SeverityBadge severity={item.severity} />
            </div>
            {item.detail && (
              <p className="mt-1 text-sm text-ribet-muted">{item.detail}</p>
            )}
            {item.suggested_action && (
              <p className="mt-2 text-xs font-medium text-ribet-green">
                → {item.suggested_action}
              </p>
            )}
            {item.gap_recommendation && (
              <p className="mt-2 rounded-lg border border-ribet-green/30 bg-ribet-green/5 px-3 py-2 text-xs text-ribet-text">
                {item.gap_recommendation}
              </p>
            )}
          </li>
        ))}
      </ul>
    </Card>
  );
}
