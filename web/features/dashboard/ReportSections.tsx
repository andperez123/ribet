import { Card } from "@/components/ui/Card";
import type { OperationalReport, ReportFinding } from "@/lib/types/report";
import { SeverityBadge } from "./SeverityBadge";

function FindingBlock({ finding }: { finding: ReportFinding }) {
  return (
    <li className="border-b border-ribet-border/60 py-4 last:border-0">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <p className="font-medium text-ribet-text">{finding.title}</p>
        {finding.severity && <SeverityBadge severity={finding.severity} />}
      </div>
      {finding.detail && (
        <p className="mt-1 text-sm text-ribet-muted">{finding.detail}</p>
      )}
      {finding.suggested_action && (
        <p className="mt-2 text-xs text-ribet-green">
          → {finding.suggested_action}
        </p>
      )}
    </li>
  );
}

function Section({
  title,
  findings,
}: {
  title: string;
  findings: ReportFinding[];
}) {
  if (!findings.length) return null;
  return (
    <Card>
      <h3 className="text-sm font-semibold text-ribet-text">{title}</h3>
      <ul className="mt-2">
        {findings.map((f, i) => (
          <FindingBlock key={`${f.title}-${i}`} finding={f} />
        ))}
      </ul>
    </Card>
  );
}

export function ReportSections({ report }: { report: OperationalReport }) {
  return (
    <div className="space-y-6">
      {report.executive_summary.length > 0 && (
        <Card>
          <h3 className="text-sm font-semibold text-ribet-text">
            Executive summary
          </h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ribet-muted">
            {report.executive_summary.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </Card>
      )}

      <Section title="Financial findings" findings={report.financial_findings} />
      <Section
        title="Operational findings"
        findings={report.operational_findings}
      />
      <Section title="Risk areas" findings={report.risk_areas} />

      {report.suggested_actions.length > 0 && (
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

      {report.trend_snapshot.length > 0 && (
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
