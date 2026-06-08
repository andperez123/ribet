import { Card } from "@/components/ui/Card";
import type { CoverageDelta, ReportContract } from "@/lib/types/report";

export function CoverageDeltaBanner({
  coverageDelta,
  confidenceScore,
}: {
  coverageDelta?: CoverageDelta | null;
  confidenceScore?: ReportContract["confidence_score"];
}) {
  if (!coverageDelta && !confidenceScore) return null;

  const message =
    coverageDelta?.message ??
    (confidenceScore && confidenceScore.delta > 0
      ? `Analysis confidence increased from ${confidenceScore.before}% to ${confidenceScore.after}%.`
      : null);

  if (!message) return null;

  return (
    <Card className="border-ribet-green/40 bg-ribet-green/10">
      <p className="text-sm font-medium text-ribet-text">
        {coverageDelta?.upload_label && (
          <span className="text-ribet-green">{coverageDelta.upload_label}: </span>
        )}
        {message}
      </p>
      {confidenceScore && confidenceScore.delta !== 0 && (
        <p className="mt-2 text-xs text-ribet-muted tabular-nums">
          Confidence {confidenceScore.before}% → {confidenceScore.after}%
          {confidenceScore.delta > 0 ? ` (+${confidenceScore.delta})` : ""}
        </p>
      )}
    </Card>
  );
}
