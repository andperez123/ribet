import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { OrgCoverage } from "@/lib/types/coverage";

type Props = {
  coverage: OrgCoverage;
};

function sectorUploadHref(_sector: string | null | undefined): string {
  return "/dashboard/upload";
}

export function ImproveAnalysisPanel({ coverage }: Props) {
  const {
    understood,
    needed,
    analysis_confidence,
    next_upload,
    gaps,
  } = coverage;

  const uploadableNeeded = needed.filter((n) => n.uploadable);

  return (
    <Card>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-ribet-text">
            Improve your analysis
          </h2>
          <p className="mt-1 text-sm text-ribet-muted">
            Ribet learns your business from ERP exports and tells you what it
            needs next.
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-wide text-ribet-muted">
            Analysis confidence
          </p>
          <p className="text-3xl font-semibold tabular-nums text-ribet-text">
            {analysis_confidence}%
          </p>
        </div>
      </div>

      {next_upload && (
        <div className="mb-6 rounded-xl border border-ribet-green/30 bg-ribet-green/10 px-4 py-3 text-sm text-ribet-text">
          Upload{" "}
          <span className="font-medium">{next_upload.label}</span> to increase
          confidence to{" "}
          <span className="font-medium tabular-nums">
            {next_upload.confidence_if_uploaded}%
          </span>
          .
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Ribet currently understands
          </p>
          {understood.length === 0 ? (
            <p className="text-sm text-ribet-muted">No exports processed yet.</p>
          ) : (
            <ul className="space-y-1.5">
              {understood.map((item) => (
                <li
                  key={item.key}
                  className="flex items-center gap-2 text-sm text-ribet-text"
                >
                  <span className="text-ribet-green" aria-hidden>
                    ✓
                  </span>
                  {item.label}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Ribet needs
          </p>
          {uploadableNeeded.length === 0 && needed.length === 0 ? (
            <p className="text-sm text-ribet-muted">
              Coverage is strong for current analysis.
            </p>
          ) : (
            <ul className="space-y-1.5">
              {(uploadableNeeded.length > 0 ? uploadableNeeded : needed).map(
                (item) => (
                  <li
                    key={item.key}
                    className="flex items-center gap-2 text-sm text-ribet-muted"
                  >
                    <span aria-hidden>○</span>
                    {item.label}
                    {!item.uploadable && (
                      <Badge variant="default" className="ml-1 text-xs">
                        coming soon
                      </Badge>
                    )}
                  </li>
                )
              )}
            </ul>
          )}
        </div>
      </div>

      {gaps.length > 0 && (
        <div className="mt-6 space-y-3 border-t border-ribet-border pt-6">
          <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Recommended next uploads
          </p>
          {gaps.slice(0, 3).map((gap) => (
            <div
              key={gap.id}
              className="rounded-xl border border-ribet-border bg-ribet-card/50 p-4"
            >
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Badge
                  variant={gap.priority === "high" ? "risk" : "default"}
                >
                  {gap.priority}
                </Badge>
                {gap.confidence_if_uploaded != null && (
                  <span className="text-xs text-ribet-muted">
                    → {gap.confidence_if_uploaded}% confidence
                  </span>
                )}
              </div>
              <p className="text-sm text-ribet-text">{gap.reason}</p>
              <ul className="mt-2 flex flex-wrap gap-2">
                {gap.recommended_uploads.map((label) => (
                  <li key={label}>
                    <Link
                      href={sectorUploadHref(gap.requested_sector)}
                      className="inline-block rounded-full border border-ribet-border px-3 py-1 text-xs font-medium text-ribet-text hover:bg-ribet-card"
                    >
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
