import Link from "next/link";
import { Suspense } from "react";
import { EmptyState } from "@/components/ui/EmptyState";
import { DashboardAutoRefresh } from "@/features/dashboard/DashboardAutoRefresh";
import { DashboardProcessingBanner } from "@/features/dashboard/DashboardProcessingBanner";
import { ExecutiveSummaryCards } from "@/features/dashboard/ExecutiveSummaryCards";
import { FindingsList } from "@/features/dashboard/FindingsList";
import { HealthComponentsGrid } from "@/features/dashboard/HealthComponentsGrid";
import { HealthScoreHero } from "@/features/dashboard/HealthScoreHero";
import { HealthTrend } from "@/features/dashboard/HealthTrend";
import { SectorProgressPanel } from "@/features/dashboard/SectorProgressPanel";
import { SnapshotKpiGrid } from "@/features/dashboard/SnapshotKpiGrid";
import { UploadsTable } from "@/features/dashboard/UploadsTable";
import { serverData } from "@/lib/api/server-data";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams?: { processing?: string };
}) {
  const [
    report,
    findings,
    healthScore,
    healthHistory,
    jobs,
    progress,
    snapshotLatest,
    snapshotHistory,
  ] = await Promise.all([
    serverData.latestReport(),
    serverData.findings(20),
    serverData.healthScore(),
    serverData.healthHistory(12),
    serverData.ingestJobs(20),
    serverData.orgProgress(),
    serverData.snapshotsLatest(),
    serverData.snapshotsHistory(12),
  ]);

  const priorSnapshot =
    snapshotHistory?.snapshots.find(
      (s) => s.period !== snapshotLatest?.period
    ) ?? null;

  const jobList = jobs?.jobs ?? [];
  const hasActiveJobs = jobList.some(
    (j) => j.status === "pending" || j.status === "processing"
  );

  return (
    <div className="space-y-8">
      <Suspense fallback={null}>
        <DashboardAutoRefresh active={hasActiveJobs} />
      </Suspense>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ribet-text md:text-3xl">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-ribet-muted">
            Operational health and findings from your latest data.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          {report && (
            <Link
              href={`/dashboard/reports/${report.id}`}
              className="rounded-full bg-ribet-green px-5 py-2.5 text-sm font-medium text-ribet-text hover:opacity-90"
            >
              View full report
            </Link>
          )}
          <Link
            href="/dashboard/reports"
            className="rounded-full border border-ribet-border px-5 py-2.5 text-sm font-medium text-ribet-text hover:bg-ribet-card"
          >
            All reports
          </Link>
        </div>
      </div>

      {!report && hasActiveJobs && (
        <DashboardProcessingBanner
          jobs={jobList}
          variant={searchParams?.processing === "demo" ? "demo" : "upload"}
        />
      )}

      {!report && !hasActiveJobs ? (
        <EmptyState
          title="No report yet"
          description="Upload ERP exports to generate your first operational health report."
          actionLabel="Upload files"
          actionHref="/#upload"
        />
      ) : report ? (
        <>
          {healthScore && <HealthScoreHero score={healthScore} />}
          {healthScore && <HealthComponentsGrid score={healthScore} />}
          <ExecutiveSummaryCards report={report} />
        </>
      ) : null}

      {snapshotLatest && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-ribet-text">
            Operational snapshot
          </h2>
          <SnapshotKpiGrid
            current={snapshotLatest}
            prior={priorSnapshot}
          />
        </section>
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
