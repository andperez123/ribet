import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { buildCoverageBreakdown } from "@/lib/dashboard/coverage-breakdown";
import { formatDate, healthStatusColor } from "@/lib/dashboard/utils";
import type { OrgCoverage } from "@/lib/types/coverage";
import type { DataCoverage, HealthScore, ReportContract } from "@/lib/types/report";

type Props = {
  reportId: string;
  healthScore: number;
  healthStatus: string;
  generatedAt: string;
  confidenceScore?: ReportContract["confidence_score"];
  orgCoverage?: OrgCoverage | null;
  coverage: DataCoverage;
  orgHealthScore?: HealthScore | null;
  variant?: "report" | "dashboard";
};

export function ReportConfidenceHeader({
  reportId,
  healthScore,
  healthStatus,
  generatedAt,
  confidenceScore,
  orgCoverage,
  coverage,
  orgHealthScore,
  variant = "report",
}: Props) {
  const confidence =
    confidenceScore?.after ?? orgCoverage?.analysis_confidence ?? null;
  const breakdown = buildCoverageBreakdown(coverage, orgCoverage);

  return (
    <div className="space-y-4">
      {variant === "report" && (
        <div>
          <Link
            href="/dashboard"
            className="text-sm font-medium text-ribet-muted hover:text-ribet-text"
          >
            ← Dashboard
          </Link>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight text-ribet-text md:text-3xl">
            Operational Health Report
          </h1>
          <p className="mt-2 text-sm text-ribet-muted">
            Generated {formatDate(generatedAt)}
          </p>
        </div>
      )}

      {variant === "dashboard" && (
        <p className="text-sm text-ribet-muted">
          Latest report · {formatDate(generatedAt)}
        </p>
      )}

      <Card className="grid gap-6 md:grid-cols-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Operational health
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-4xl font-semibold tabular-nums text-ribet-text">
              {orgHealthScore?.score ?? healthScore}
            </span>
            <span className="text-lg text-ribet-muted">/ 100</span>
            <Badge
              variant={
                healthStatus.toLowerCase().includes("risk") ||
                healthStatus.toLowerCase().includes("critical")
                  ? "risk"
                  : "success"
              }
              className={healthStatusColor(healthStatus)}
            >
              {orgHealthScore?.status ?? healthStatus}
            </Badge>
          </div>
        </div>

        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Analysis confidence
          </p>
          <p className="mt-2 text-4xl font-semibold tabular-nums text-ribet-text">
            {confidence != null ? `${confidence}%` : "—"}
          </p>
          {confidenceScore && confidenceScore.delta !== 0 && (
            <p className="mt-1 text-xs text-ribet-muted tabular-nums">
              {confidenceScore.before}% → {confidenceScore.after}%
              {confidenceScore.delta > 0 ? ` (+${confidenceScore.delta})` : ""}
            </p>
          )}
        </div>
      </Card>

      {(breakdown.understood.length > 0 || breakdown.missing.length > 0) && (
        <Card className="space-y-3 text-sm">
          {breakdown.understood.length > 0 && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
                Based on
              </p>
              <p className="mt-1 text-ribet-text">
                {breakdown.understood.map((label) => (
                  <span key={label} className="mr-3 inline-flex items-center gap-1">
                    <span className="text-ribet-green" aria-hidden>
                      ✓
                    </span>
                    {label}
                  </span>
                ))}
              </p>
            </div>
          )}
          {breakdown.missing.length > 0 && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
                Missing
              </p>
              <p className="mt-1 text-ribet-muted">
                {breakdown.missing.map((label) => (
                  <span key={label} className="mr-3 inline-flex items-center gap-1">
                    <span aria-hidden>○</span>
                    {label}
                  </span>
                ))}
              </p>
            </div>
          )}
        </Card>
      )}

      {variant === "report" && (
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <a
            href={`/api/reports/${reportId}/pdf`}
            className="font-medium text-ribet-green hover:underline"
            download
          >
            Download PDF
          </a>
        </div>
      )}
    </div>
  );
}
