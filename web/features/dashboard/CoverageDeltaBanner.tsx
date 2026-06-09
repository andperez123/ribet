import { Card } from "@/components/ui/Card";
import type { CoverageDelta, ReportContract, UnlocksFromUpload } from "@/lib/types/report";

function normalizeUnlocks(
  unlocks?: ReportContract["unlocks_from_this_upload"]
): UnlocksFromUpload | null {
  if (!unlocks) return null;
  if (Array.isArray(unlocks)) {
    return { unlocked: unlocks, still_gated: [] };
  }
  return unlocks;
}

export function CoverageDeltaBanner({
  coverageDelta,
  confidenceScore,
  unlocks,
}: {
  coverageDelta?: CoverageDelta | null;
  confidenceScore?: ReportContract["confidence_score"];
  unlocks?: ReportContract["unlocks_from_this_upload"];
}) {
  if (!coverageDelta && !confidenceScore) return null;

  const split = normalizeUnlocks(unlocks);
  const uploadLabel = coverageDelta?.upload_label;
  const confidenceAfter = confidenceScore?.after;
  const confidenceBefore = confidenceScore?.before;
  const confidenceDelta = confidenceScore?.delta ?? 0;

  let headline = coverageDelta?.message;
  if (!headline && uploadLabel && confidenceScore) {
    headline =
      confidenceDelta > 0
        ? `You uploaded ${uploadLabel}. Ribet expanded your operational picture and raised analysis confidence.`
        : `You uploaded ${uploadLabel}. Ribet refreshed analysis for this data.`;
  }

  if (!headline) return null;

  return (
    <Card className="border-ribet-green/40 bg-ribet-green/10 space-y-3">
      <p className="text-sm font-medium text-ribet-text">
        {uploadLabel && (
          <span className="text-ribet-green">↑ {uploadLabel} · </span>
        )}
        {headline.replace(/^You uploaded [^.]+\.\s*/, "") || headline}
      </p>
      {confidenceScore && (
        <p className="text-sm text-ribet-text tabular-nums">
          Analysis confidence{" "}
          <span className="font-semibold">
            {confidenceBefore}% → {confidenceAfter}%
          </span>
          {confidenceDelta > 0 ? ` (+${confidenceDelta}%)` : ""}
        </p>
      )}
      {split?.unlocked?.length ? (
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
            New from this upload
          </p>
          <ul className="mt-1 space-y-1 text-sm text-ribet-text">
            {split.unlocked.slice(0, 3).map((u) => (
              <li key={u.message} className="flex gap-2">
                <span className="text-ribet-green" aria-hidden>
                  ✓
                </span>
                {u.message}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {split?.still_gated?.length ? (
        <p className="text-xs text-ribet-muted">
          Still gated: {split.still_gated.map((g) => g.message).join(" · ")}
        </p>
      ) : null}
    </Card>
  );
}
