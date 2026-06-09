import type { SignalTrace } from "@/lib/types/report";

type Props = {
  trace?: SignalTrace | null;
  sourceLabel?: string | null;
  findingId?: string | null;
  metricKey?: string | null;
  evidenceVerified?: boolean;
  className?: string;
};

export function SourceTraceabilityChip({
  trace,
  sourceLabel,
  findingId,
  metricKey,
  evidenceVerified,
  className = "",
}: Props) {
  const source =
    trace?.upload_label ?? sourceLabel?.split("·")[0]?.replace("Based on:", "").trim();
  const finding = trace?.finding_id ?? findingId;
  const metric = trace?.metric_keys?.[0] ?? metricKey;
  const verified =
    evidenceVerified ??
    (trace?.evidence_verified === true ||
      (trace?.evidence_verified !== false && Boolean(finding)));

  const parts: string[] = [];
  if (source) parts.push(`Source: ${source}`);
  if (finding) parts.push(`Finding: ${finding}`);
  if (metric) parts.push(`Metric: ${metric}`);
  parts.push(`Evidence: ${verified ? "Verified" : "Not linked"}`);

  if (parts.length <= 1 && !source && !finding) return null;

  return (
    <p
      className={`font-mono text-xs text-ribet-muted ${className}`}
      aria-label="Source traceability"
    >
      {parts.join(" · ")}
    </p>
  );
}
