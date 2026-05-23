import Link from "next/link";
import { EmptyState } from "@/components/ui/EmptyState";
import { ExecutiveSummaryCards } from "@/features/dashboard/ExecutiveSummaryCards";
import { FindingsList } from "@/features/dashboard/FindingsList";
import { HealthComponentsGrid } from "@/features/dashboard/HealthComponentsGrid";
import { HealthScoreHero } from "@/features/dashboard/HealthScoreHero";
import { HealthTrend } from "@/features/dashboard/HealthTrend";
import { SectorProgressPanel } from "@/features/dashboard/SectorProgressPanel";
import { UploadsTable } from "@/features/dashboard/UploadsTable";
import { serverData } from "@/lib/api/server-data";

export default async function DashboardPage() {
  const [report, findings, healthScore, healthHistory, jobs, progress] =
    await Promise.all([
      serverData.latestReport(),
      serverData.findings(20),
      serverData.healthScore(),
      serverData.healthHistory(12),
      serverData.ingestJobs(20),
      serverData.orgProgress(),
    ]);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-rivet-text md:text-3xl">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-rivet-muted">
            Operational health and findings from your latest data.
          </p>
        </div>
        {report && (
          <Link
            href={`/dashboard/reports/${report.id}`}
            className="rounded-full bg-rivet-green px-5 py-2.5 text-sm font-medium text-rivet-text hover:opacity-90"
          >
            View full report
          </Link>
        )}
      </div>

      {!report ? (
        <EmptyState
          title="No report yet"
          description="Upload ERP exports to generate your first operational health report."
          actionLabel="Upload files"
          actionHref="/#upload"
        />
      ) : (
        <>
          {healthScore && <HealthScoreHero score={healthScore} />}
          {healthScore && <HealthComponentsGrid score={healthScore} />}
          <ExecutiveSummaryCards report={report} />
        </>
      )}

      {healthHistory && healthHistory.snapshots.length > 1 && (
        <HealthTrend history={healthHistory} />
      )}

      {progress && (
        <SectorProgressPanel
          progress={progress}
          findings={findings ?? undefined}
        />
      )}

      {jobs && <UploadsTable jobs={jobs.jobs} />}

      {findings && findings.length > 0 && (
        <FindingsList findings={findings} />
      )}
    </div>
  );
}
