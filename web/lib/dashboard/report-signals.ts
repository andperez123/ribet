import { severityRank } from "@/lib/dashboard/utils";
import type {
  DomainInsight,
  Finding,
  InsightSeverity,
  OperationalReport,
  ReportContract,
  SignalTrace,
  TopSignal,
} from "@/lib/types/report";

const INSIGHT_SEVERITY_RANK: Record<InsightSeverity, number> = {
  alert: 0,
  watch: 1,
  info: 2,
};

const REPORT_TYPE_LABELS: Record<string, string> = {
  ar_aging: "AR Aging",
  ap_aging: "AP Aging",
  gl_detail: "GL Detail",
  gl_trial_balance: "GL Trial Balance",
  inventory: "Inventory",
};

function insightSeverityRank(severity: InsightSeverity): number {
  return INSIGHT_SEVERITY_RANK[severity] ?? 3;
}

export function sortDomainInsights(insights: DomainInsight[]): DomainInsight[] {
  return [...insights].sort(
    (a, b) => insightSeverityRank(a.severity) - insightSeverityRank(b.severity)
  );
}

function findingByTitle(findings: Finding[], title: string): Finding | undefined {
  return findings.find((f) => f.title === title);
}

function traceForFinding(
  f: Finding,
  contractTrace?: SignalTrace | null,
  hasEvidencePack?: boolean
): SignalTrace {
  const domainSource =
    f.department === "finance" || f.category === "financial"
      ? "AR Aging"
      : f.category === "operational"
        ? "Inventory"
        : undefined;
  return {
    upload_label:
      contractTrace?.upload_label ??
      domainSource ??
      REPORT_TYPE_LABELS[f.finding_type?.split("_")[0] ?? ""] ??
      "Upload",
    period: contractTrace?.period,
    row_count: contractTrace?.row_count,
    job_id: contractTrace?.job_id,
    finding_id: f.finding_id ?? undefined,
    evidence_verified: hasEvidencePack && Boolean(f.finding_id),
  };
}

export function buildTopSignals(
  report: OperationalReport,
  findings: Finding[]
): TopSignal[] {
  const contractTrace = report.report_contract?.source_traceability;
  const hasEvidence = Boolean(report.evidence_pack);

  if (report.report_contract?.top_signals?.length) {
    return report.report_contract.top_signals.slice(0, 3).map((s) => ({
      ...s,
      why_it_matters: s.why_it_matters ?? s.body,
      source_trace: s.source_trace ?? (s.finding_id ? { finding_id: s.finding_id, evidence_verified: hasEvidence } : null),
    }));
  }

  const signals: TopSignal[] = [];

  for (const f of [...findings].sort(
    (a, b) => severityRank(a.severity) - severityRank(b.severity)
  )) {
    if (signals.length >= 3) break;
    signals.push({
      kind: "finding",
      title: f.title,
      body: f.narrative || f.detail,
      why_it_matters: f.business_impact || f.detail,
      severity: f.severity ?? "medium",
      suggested_action: f.recommendation || f.suggested_action || undefined,
      finding_id: f.finding_id ?? undefined,
      source_trace: traceForFinding(f, contractTrace, hasEvidence),
    });
  }

  for (const insight of sortDomainInsights(report.domain_insights ?? [])) {
    if (signals.length >= 3) break;
    if (insight.severity === "info" && signals.length >= 2) continue;
    signals.push({
      kind: "insight",
      title: insight.title,
      body: insight.body,
      why_it_matters: insight.body,
      severity: insight.severity,
      metric_label: insight.metric_label ?? undefined,
      metric_value: insight.metric_value ?? undefined,
      source: insight.source_label ?? undefined,
      source_trace: contractTrace
        ? { ...contractTrace, metric_keys: insight.metric_label ? [insight.metric_label] : undefined }
        : null,
    });
  }

  for (const line of report.executive_summary ?? []) {
    if (signals.length >= 3) break;
    if (signals.some((s) => s.title === line || s.body === line)) continue;
    signals.push({
      kind: "executive",
      title: "Executive summary",
      body: line,
      why_it_matters: line,
      severity: "medium",
    });
  }

  return signals.slice(0, 3);
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

export function signalSeverityPill(severity: string): "High" | "Medium" | "Low" {
  const s = severity.toLowerCase();
  if (s === "critical" || s === "high" || s === "alert") return "High";
  if (s === "medium" || s === "watch") return "Medium";
  return "Low";
}

export function findingForSignal(
  signal: TopSignal,
  findings: Finding[]
): Finding | undefined {
  if (signal.finding_id) {
    return findings.find((f) => f.finding_id === signal.finding_id);
  }
  return findingByTitle(findings, signal.title);
}
