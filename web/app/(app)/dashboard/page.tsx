import Link from "next/link";
import { Suspense } from "react";
import { EmptyState } from "@/components/ui/EmptyState";
import { AgentIntelligenceRail } from "@/features/agents/AgentIntelligenceRail";
import { AgentsWaitingPanel } from "@/features/agents/AgentsWaitingPanel";
import { SectorCoverageMap } from "@/features/agents/SectorCoverageMap";
import { DashboardAutoRefresh } from "@/features/dashboard/DashboardAutoRefresh";
import { DashboardFailedJobsBanner } from "@/features/dashboard/DashboardFailedJobsBanner";
import { DashboardProcessingBanner } from "@/features/dashboard/DashboardProcessingBanner";
import { FindingsList } from "@/features/dashboard/FindingsList";
import { HealthTrend } from "@/features/dashboard/HealthTrend";
import { ReportConfidenceHeader } from "@/features/dashboard/ReportConfidenceHeader";
import { TopSignalsHero } from "@/features/dashboard/TopSignalsHero";
import { UploadsTable } from "@/features/dashboard/UploadsTable";
import { serverData } from "@/lib/api/server-data";
import { buildTopSignals } from "@/lib/dashboard/report-signals";

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
    orgCoverage,
  ] = await Promise.all([
    serverData.latestReport(),
    serverData.findings(20),
    serverData.healthScore(),
    serverData.healthHistory(12),
    serverData.ingestJobs(20),
    serverData.orgProgress(),
    serverData.orgCoverage(),
  ]);

  const jobList = jobs?.jobs ?? [];
  const hasActiveJobs = jobList.some(
    (j) => j.status === "pending" || j.status === "processing"
  );
  const hasFailedJobs = jobList.some((j) => j.status === "error");
  const contract = report?.report_contract;
  const topSignals = report ? buildTopSignals(report, findings ?? []) : [];

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
            Operational health and intelligence from your latest data.
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

      {hasFailedJobs && <DashboardFailedJobsBanner jobs={jobList} />}

      {!report && !hasActiveJobs ? (
        <EmptyState
          title="No report yet"
          description="Upload ERP exports to generate your first operational health report."
          actionLabel="Upload files"
          actionHref="/#upload"
        />
      ) : report ? (
        <>
          <ReportConfidenceHeader
            reportId={report.id}
            healthScore={report.health_score}
            healthStatus={report.health_status}
            generatedAt={report.generated_at}
            confidenceScore={contract?.confidence_score}
            orgCoverage={orgCoverage}
            coverage={{
              ar: report.data_coverage?.ar ?? false,
              ap: report.data_coverage?.ap ?? false,
              gl: report.data_coverage?.gl ?? false,
              inventory: report.data_coverage?.inventory ?? false,
            }}
            orgHealthScore={healthScore}
            variant="dashboard"
          />
          {contract?.agent_roster?.length ? (
            <AgentIntelligenceRail agents={contract.agent_roster} />
          ) : null}
          {topSignals.length > 0 && <TopSignalsHero signals={topSignals} />}
          <AgentsWaitingPanel
            agents={contract?.agent_roster}
            blockedAnalyses={contract?.blocked_analyses}
          />
        </>
      ) : null}

      {healthHistory && healthHistory.snapshots.length > 1 && (
        <HealthTrend history={healthHistory} />
      )}

      {progress && (
        <SectorCoverageMap
          progress={progress}
          agentRoster={contract?.agent_roster}
        />
      )}

      {jobs && <UploadsTable jobs={jobs.jobs} />}

      {findings && findings.length > 0 && (
        <FindingsList findings={findings} />
      )}
    </div>
  );
}
