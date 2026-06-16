"use client";

import { Card } from "@/components/ui/Card";
import type { BlockedAnalysis, SetupPreview, SetupWarning } from "@/lib/types/report";

export function SetupPreviewPanel({
  preview,
  warnings,
}: {
  preview?: SetupPreview | null;
  warnings?: SetupWarning[];
}) {
  const allWarnings = [...(warnings ?? []), ...(preview?.warnings ?? [])];
  const blocked = preview?.blocked_analyses ?? [];

  if (!preview && !allWarnings.length) return null;

  return (
    <Card className="space-y-4 border-dashed">
      <div>
        <h2 className="text-sm font-semibold text-ribet-text">Coverage preview</h2>
        <p className="mt-1 text-xs text-ribet-muted">
          What this selection unlocks or blocks before you regenerate.
        </p>
      </div>

      {allWarnings.length > 0 && (
        <ul className="space-y-2">
          {allWarnings.map((w) => (
            <li
              key={`${w.code}-${w.message}`}
              className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-sm text-ribet-text"
            >
              {w.message}
            </li>
          ))}
        </ul>
      )}

      {preview && (
        <dl className="grid gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-xs text-ribet-muted">Domains</dt>
            <dd className="mt-1 text-ribet-text">
              {preview.domains_covered.length
                ? preview.domains_covered.join(", ")
                : "None"}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-ribet-muted">Sectors</dt>
            <dd className="mt-1 text-ribet-text">
              {preview.sectors_covered.length
                ? preview.sectors_covered.join(", ")
                : "None"}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-ribet-muted">Analysis confidence</dt>
            <dd className="mt-1 tabular-nums text-ribet-text">
              {preview.analysis_confidence}%
            </dd>
          </div>
        </dl>
      )}

      {blocked.length > 0 && (
        <div>
          <h3 className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Blocked analyses
          </h3>
          <ul className="mt-2 space-y-2">
            {blocked.map((item: BlockedAnalysis) => (
              <li
                key={`${item.analysis_name}-${item.reason_code}`}
                className="rounded-lg border border-ribet-border/60 px-3 py-2 text-sm"
              >
                <p className="font-medium text-ribet-text">{item.analysis_name}</p>
                <p className="mt-0.5 text-ribet-muted">{item.reason}</p>
                {item.requires_uploads.length > 0 && (
                  <p className="mt-1 text-xs text-ribet-muted">
                    Needs: {item.requires_uploads.join(", ")}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
