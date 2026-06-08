import { severityRank } from "@/lib/dashboard/utils";
import type {
  DomainInsight,
  Finding,
  InsightSeverity,
  OperationalReport,
  ReportContract,
  TopSignal,
} from "@/lib/types/report";

const INSIGHT_SEVERITY_RANK: Record<InsightSeverity, number> = {
  alert: 0,
  watch: 1,
  info: 2,
};

function insightSeverityRank(severity: InsightSeverity): number {
  return INSIGHT_SEVERITY_RANK[severity] ?? 3;
}

export function sortDomainInsights(insights: DomainInsight[]): DomainInsight[] {
  return [...insights].sort(
    (a, b) => insightSeverityRank(a.severity) - insightSeverityRank(b.severity)
  );
}

export function buildTopSignals(
  report: OperationalReport,
  findings: Finding[]
): TopSignal[] {
  if (report.report_contract?.top_signals?.length) {
    return report.report_contract.top_signals.slice(0, 5);
  }

  const signals: TopSignal[] = [];

  for (const f of [...findings].sort(
    (a, b) => severityRank(a.severity) - severityRank(b.severity)
  )) {
    if (signals.length >= 5) break;
    signals.push({
      kind: "finding",
      title: f.title,
      body: f.narrative || f.detail,
      severity: f.severity ?? "medium",
      suggested_action: f.recommendation || f.suggested_action || undefined,
      source: undefined,
    });
  }

  for (const insight of sortDomainInsights(report.domain_insights ?? [])) {
    if (signals.length >= 5) break;
    if (insight.severity === "info" && signals.length >= 3) continue;
    signals.push({
      kind: "insight",
      title: insight.title,
      body: insight.body,
      severity: insight.severity,
      metric_label: insight.metric_label ?? undefined,
      metric_value: insight.metric_value ?? undefined,
      source: insight.source_label ?? undefined,
    });
  }

  for (const line of report.executive_summary ?? []) {
    if (signals.length >= 5) break;
    if (signals.some((s) => s.title === line || s.body === line)) continue;
    signals.push({
      kind: "executive",
      title: "Executive summary",
      body: line,
      severity: "medium",
    });
  }

  return signals.slice(0, 5);
}

export function getActionItems(
  report: OperationalReport,
  findings: Finding[]
): ReportContract["action_items"] {
  if (report.report_contract?.action_items?.length) {
    return report.report_contract.action_items;
  }

  return [...findings]
    .sort((a, b) => severityRank(a.severity) - severityRank(b.severity))
    .slice(0, 10)
    .map((f) => ({
      title: f.title,
      detail: f.narrative || f.detail,
      severity: f.severity ?? "medium",
      suggested_action: f.recommendation || f.suggested_action || undefined,
      gap_recommendation: f.gap_recommendation || undefined,
      finding_type: f.finding_type,
    }));
}

export function signalSeverityClass(severity: string): string {
  const s = severity.toLowerCase();
  if (s === "critical" || s === "high" || s === "alert") {
    return "border-ribet-risk/60 bg-ribet-risk/10";
  }
  if (s === "medium" || s === "watch") {
    return "border-amber-500/50 bg-amber-500/10";
  }
  return "border-ribet-border bg-ribet-card";
}
