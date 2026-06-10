import Link from "next/link";
import { Suspense } from "react";
import { AgentIntelligenceRail } from "@/features/agents/AgentIntelligenceRail";
import { AgentsWaitingPanel } from "@/features/agents/AgentsWaitingPanel";
import { DashboardAutoRefresh } from "@/features/dashboard/DashboardAutoRefresh";
import { DashboardFailedJobsBanner } from "@/features/dashboard/DashboardFailedJobsBanner";
import { DashboardProcessingBanner } from "@/features/dashboard/DashboardProcessingBanner";
import {
  DashboardEmptyHero,
  DashboardProcessingState,
  DataNoReportState,
} from "@/features/dashboard/DashboardStatePanels";
import { DomainStoryGrid } from "@/features/dashboard/DomainStoryGrid";
import { FindingsList } from "@/features/dashboard/FindingsList";
import { NarrationSetupBanner } from "@/features/dashboard/NarrationSetupBanner";
import { NarrativeStory } from "@/features/dashboard/NarrativeStory";
import { OperationsChatPanel } from "@/features/dashboard/OperationsChatPanel";
import { StoryHero } from "@/features/dashboard/StoryHero";
import { TrajectoryRow } from "@/features/dashboard/TrajectoryRow";
import { UnlockRail } from "@/features/dashboard/UnlockRail";
import { PartialDataHero } from "@/features/dashboard/PartialDataHero";
import { UploadsTable } from "@/features/dashboard/UploadsTable";
import { getDashboardMode } from "@/lib/dashboard/mode";
import { buildTopSignals } from "@/lib/dashboard/report-signals";
import { serverData } from "@/lib/api/server-data";
import type { DataCoverage, DataDigest } from "@/lib/types/report";

const EMPTY_DIGEST: DataDigest = {
  ar_total: 0,
  ar_over_90: 0,
  ar_over_90_pct: 0,
  ar_invoice_count: 0,
  top_customers: [],
  ap_total: 0,
  ap_negative_total: 0,
  vendor_count: 0,
  top_vendors: [],
  ap_current: 0,
  ap_1_30: 0,
  ap_31_60: 0,
  ap_61_90: 0,
  ap_91_plus: 0,
  ap_over_60_pct: 0,
  gl_txn_count: 0,
  gl_adjustment_total: 0,
  gl_unmapped_count: 0,
  inventory_item_count: 0,
  inventory_total_qty: 0,
  inventory_negative_count: 0,
  inventory_zero_count: 0,
  inventory_orphan_count: 0,
  po_count: 0,
  po_open_total: 0,
  po_late_count: 0,
  po_late_total: 0,
  top_late_pos: [],
  so_count: 0,
  so_open_total: 0,
  so_past_due_count: 0,
  so_past_due_total: 0,
  top_past_due_orders: [],
};

const EMPTY_COVERAGE: DataCoverage = {
  ar: false,
  ap: false,
  gl: false,
  inventory: false,
  ar_present: false,
  ar_unmapped: false,
  ap_aging_available: false,
  primary_domain: null,
};

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
    weeklyBrief,
    snapshot,
  ] = await Promise.all([
    serverData.latestReport(),
    serverData.findings(20),
    serverData.healthScore(),
    serverData.healthHistory(12),
    serverData.ingestJobs(20),
    serverData.orgProgress(),
    serverData.orgCoverage(),
    serverData.weeklyBrief(),
    serverData.snapshotsLatest(),
  ]);

  const jobList = jobs?.jobs ?? [];
  const hasActiveJobs = jobList.some(
    (j) => j.status === "pending" || j.status === "processing"
  );
  const hasFailedJobs = jobList.some((j) => j.status === "error");
  const hasDoneJobs = jobList.some((j) => j.status === "done");
  const contract = report?.report_contract;
  const topSignals = report ? buildTopSignals(report, findings ?? []) : [];

  const digest = {
    ...EMPTY_DIGEST,
    ...(contract?.digest_kpis ?? report?.data_digest ?? {}),
  };
  const coverage = {
    ...EMPTY_COVERAGE,
    ...(report?.data_coverage ?? {}),
  };

  const mode = getDashboardMode({
    report,
    jobs: jobList,
    orgCoverage,
    digest,
  });

  const healthSparkline =
    healthHistory?.snapshots?.map((s) => s.score) ?? undefined;

  const unlocksRaw = contract?.unlocks_from_this_upload;
  const unlocks = Array.isArray(unlocksRaw)
    ? unlocksRaw
    : unlocksRaw && "unlocked" in unlocksRaw
      ? unlocksRaw.unlocked
      : null;

  return (
    <div className="space-y-10">
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
            href="/dashboard/upload"
            className="rounded-full border border-ribet-border px-5 py-2.5 text-sm font-medium text-ribet-text hover:bg-ribet-card"
          >
            Upload files
          </Link>
          <Link
            href="/dashboard/reports"
            className="rounded-full border border-ribet-border px-5 py-2.5 text-sm font-medium text-ribet-text hover:bg-ribet-card"
          >
            All reports
          </Link>
        </div>
      </div>

      <NarrationSetupBanner />

      {hasFailedJobs && <DashboardFailedJobsBanner jobs={jobList} />}

      {mode === "empty" && <DashboardEmptyHero />}

      {mode === "processing" && (
        <>
          {!report && searchParams?.processing === "demo" ? (
            <DashboardProcessingBanner
              jobs={jobList}
              variant="demo"
            />
          ) : (
            <DashboardProcessingState jobs={jobList} />
          )}
        </>
      )}

      {mode === "data_no_report" && orgCoverage && (
        <>
          <PartialDataHero orgCoverage={orgCoverage} snapshot={snapshot} />
          <DataNoReportState
            orgCoverage={orgCoverage}
            hasDoneJobs={hasDoneJobs}
          />
        </>
      )}

      {mode === "report" && report && (
        <>
          <StoryHero
            report={report}
            digest={digest}
            coverage={coverage}
            orgCoverage={orgCoverage}
            analystOutput={report.analyst_output}
            confidenceScore={contract?.confidence_score ?? undefined}
            healthSparkline={healthSparkline}
          />

          <NarrativeStory
            analystOutput={report.analyst_output}
            topSignals={topSignals}
            reportId={report.id}
          />

          <DomainStoryGrid
            digest={digest}
            coverage={coverage}
            analystOutput={report.analyst_output}
          />

          {contract?.agent_roster?.length ? (
            <AgentIntelligenceRail agents={contract.agent_roster} />
          ) : null}

          <AgentsWaitingPanel
            agents={contract?.agent_roster}
            blockedAnalyses={contract?.blocked_analyses}
          />

          <TrajectoryRow
            healthHistory={healthHistory}
            healthScore={healthScore}
            weeklyBrief={weeklyBrief}
          />

          <OperationsChatPanel reportId={report.id} />
        </>
      )}

      {orgCoverage && (
        <UnlockRail
          coverage={orgCoverage}
          analystOutput={report?.analyst_output}
          unlocks={unlocks}
        />
      )}

      {jobs && (
        <UploadsTable jobs={jobs.jobs} limit={5} showViewAll />
      )}

      {findings && findings.length > 0 && mode === "report" && (
        <FindingsList findings={findings} />
      )}
    </div>
  );
}
