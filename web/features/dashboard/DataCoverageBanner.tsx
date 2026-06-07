import { Card } from "@/components/ui/Card";
import { formatCoverageSummary } from "@/lib/dashboard/utils";
import type { DataCoverage, DataDigest } from "@/lib/types/report";

export function DataCoverageBanner({
  coverage,
  digest,
}: {
  coverage: DataCoverage;
  digest?: DataDigest;
}) {
  const message = formatCoverageSummary(coverage, digest);
  if (!message) return null;

  const analyzed = Object.entries(coverage).filter(([, v]) => v).length;
  const total = Object.keys(coverage).length;

  return (
    <Card className="border-ribet-green/30 bg-ribet-green/5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Data analyzed
          </p>
          <p className="mt-1 text-sm text-ribet-text">{message}</p>
        </div>
        <p className="text-xs text-ribet-muted">
          {analyzed} of {total} domains
        </p>
      </div>
    </Card>
  );
}
