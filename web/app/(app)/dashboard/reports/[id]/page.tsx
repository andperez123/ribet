import Link from "next/link";
import { notFound } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { AgentIntelligenceRail } from "@/features/agents/AgentIntelligenceRail";
import { BlockedAnalysesPanel } from "@/features/dashboard/BlockedAnalysesPanel";
import { CoverageDeltaBanner } from "@/features/dashboard/CoverageDeltaBanner";
import { DeleteReportButton } from "@/features/dashboard/DeleteReportButton";
import { DashboardBriefingPanel } from "@/features/dashboard/DashboardBriefingPanel";
import { ExecutiveInsightsBar } from "@/features/dashboard/ExecutiveInsightsBar";
import { EvidencePackPanel } from "@/features/dashboard/EvidencePackPanel";
import { EvidenceSummaryPanel } from "@/features/dashboard/EvidenceSummaryPanel";
import { ExecutiveAnalysisPanel } from "@/features/dashboard/ExecutiveAnalysisPanel";
import { HealthComponentsGrid } from "@/features/dashboard/HealthComponentsGrid";
import { ImproveAnalysisPanel } from "@/features/dashboard/ImproveAnalysisPanel";
import { InsightCardsGrid } from "@/features/dashboard/InsightCardsGrid";
import { NarrationSetupBanner } from "@/features/dashboard/NarrationSetupBanner";
import { OperationsChatPanel } from "@/features/dashboard/OperationsChatPanel";
import { OperationalCharts } from "@/features/dashboard/OperationalCharts";
import { ReportActionItems } from "@/features/dashboard/ReportActionItems";
import { ReportAnalysisDebugPanel } from "@/features/dashboard/ReportAnalysisDebugPanel";
import { ReportConfidenceHeader } from "@/features/dashboard/ReportConfidenceHeader";
import { ReportFindingsList } from "@/features/dashboard/ReportFindingsList";
import { EvidencePackEditor } from "@/features/dashboard/report-setup/EvidencePackEditor";
import { ReportNarrativeEditor } from "@/features/dashboard/report-setup/ReportNarrativeEditor";
import { ReportSourcesUsedPanel } from "@/features/dashboard/report-setup/ReportSourcesUsedPanel";
import {
  OrgWideSynthesisPanel,
  PrimaryAnalysisPanel,
} from "@/features/dashboard/ReportAnalysisSections";
import { ReportSections } from "@/features/dashboard/ReportSections";
import { TopEntitiesPanel } from "@/features/dashboard/TopEntitiesPanel";
import { TopSignalsHero } from "@/features/dashboard/TopSignalsHero";
import { UnlocksFromUploadPanel } from "@/features/dashboard/UnlocksFromUploadPanel";
import { WeeklyBriefPanel } from "@/features/dashboard/WeeklyBriefPanel";
import { isAdminView } from "@/lib/admin/is-admin-view";
import { serverData } from "@/lib/api/server-data";
import {
  buildTopSignals,
  getActionItems,
  sortDomainInsights,
} from "@/lib/dashboard/report-signals";
import { resolveDashboardBriefing } from "@/lib/dashboard/briefing";
import { digestHasData } from "@/lib/dashboard/utils";
import { metricTakeawaysMap } from "@/lib/dashboard/metric-takeaways";
import { selectInsightMetrics } from "@/lib/dashboard/insight-metrics";
import { deriveReportDigestCoverage } from "@/lib/dashboard/org-digest";
import type {
  AnalysisMetadata,
  AnalystOutput,
  DataCoverage,
  DataDigest,
  DomainInsight,
} from "@/lib/types/report";

type Props = { params: Promise<{ id: string }> };

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
  purchase_orders: false,
  sales_orders: false,
  ar_present: false,
  ar_unmapped: false,
  ap_aging_available: false,
  primary_domain: null,
};

const EMPTY_METADATA: AnalysisMetadata = {
  narration: "legacy",
  finding_count: 0,
  narrated_count: 0,
  data_domains_present: [],
};

export default async function ReportPage({ params }: Props) {
  const { id } = await params;
  const [report, healthScore, findings, orgCoverage, showAdmin, weeklyBrief] = await Promise.all([
    serverData.report(id),
    serverData.healthScore(),
    serverData.findings(50, id),
    serverData.orgCoverage(),
    isAdminView(),
    serverData.weeklyBrief(id),
  ]);

  if (!report) notFound();

  const contract = report.report_contract;
  const analystOutput = (report.analyst_output ?? null) as AnalystOutput | null;
  const { digest, coverage } = deriveReportDigestCoverage(
    report,
    EMPTY_DIGEST,
    EMPTY_COVERAGE
  );
  const insightMetrics = selectInsightMetrics(digest, coverage);
  const metricTakeaways = metricTakeawaysMap(analystOutput);
  const insights: DomainInsight[] = sortDomainInsights(
    contract?.domain_insights ?? report.domain_insights ?? []
  );
  const metadata = report.analysis_metadata ?? EMPTY_METADATA;
  const hasData = digestHasData(digest);
  const topSignals = buildTopSignals(report, findings ?? []);
  const actionItems = getActionItems(report, findings ?? []);
  const hasEvidencePack = Boolean(report.evidence_pack);
  const verifiedFindings = topSignals.map((s) => s.title);

  if (hasData && insights.length === 0) {
    console.error(
      `[report-page] Insight invariant: digest has data but domain_insights is empty (report ${id})`
    );
  }

  return (
    <div className="space-y-8">
      <ReportConfidenceHeader
        reportId={report.id}
        healthScore={report.health_score}
        healthStatus={report.health_status}
        generatedAt={report.generated_at}
        confidenceScore={contract?.confidence_score}
        orgCoverage={orgCoverage}
        coverage={coverage}
        orgHealthScore={healthScore}
      />

      <div className="flex flex-wrap gap-3">
        <Link
          href="/dashboard/reports/setup"
          className="rounded-full border border-ribet-border px-5 py-2.5 text-sm font-medium text-ribet-text hover:bg-ribet-card"
        >
          Sources &amp; assumptions
        </Link>
        <DeleteReportButton reportId={report.id} redirectTo="/dashboard/reports" />
      </div>

      {report.sources && report.sources.length > 0 && (
        <ReportSourcesUsedPanel sources={report.sources} />
      )}

      <NarrationSetupBanner />

      {(contract?.coverage_delta || contract?.confidence_score) && (
        <CoverageDeltaBanner
          coverageDelta={contract?.coverage_delta}
          confidenceScore={contract?.confidence_score}
          unlocks={contract?.unlocks_from_this_upload}
        />
      )}

      {contract?.agent_roster?.length ? (
        <AgentIntelligenceRail agents={contract.agent_roster} />
      ) : null}

      {!hasData && (
        <Card className="border-dashed">
          <p className="text-sm text-ribet-muted">
            {report.executive_summary[0] ??
              "Upload AR, AP, GL, or inventory exports to generate operational insights."}
          </p>
          <Link
            href="/dashboard/upload"
            className="mt-4 inline-block text-sm font-medium text-ribet-green hover:opacity-90"
          >
            Upload files →
          </Link>
        </Card>
      )}

      {hasData && (
        <>
          <TopSignalsHero
            signals={topSignals}
            evidenceAnchorHref={hasEvidencePack ? "#evidence-pack-detail" : undefined}
          />

          <DashboardBriefingPanel
            briefing={resolveDashboardBriefing(analystOutput)}
            source={analystOutput?.source}
          />

          <ExecutiveInsightsBar
            metrics={insightMetrics}
            takeaways={metricTakeaways}
            title="Report at a glance"
            subtitle="Key signals from this report's verified data."
            orgCoverage={orgCoverage}
          />

          {healthScore && (
            <HealthComponentsGrid
              score={healthScore}
              analystOutput={analystOutput}
            />
          )}

          <OperationalCharts digest={digest} coverage={coverage} />
          <TopEntitiesPanel digest={digest} coverage={coverage} />

          <EvidenceSummaryPanel
            digest={digest}
            coverage={coverage}
            metadata={metadata}
            rulesExecuted={findings?.length}
            evidenceSummary={contract?.evidence_summary}
            hasEvidencePack={hasEvidencePack}
            showAdminLink={showAdmin}
          />

          <BlockedAnalysesPanel
            blockedAnalyses={contract?.blocked_analyses}
            coverageGaps={contract?.coverage_gaps}
            analystOutput={analystOutput}
          />

          <ReportActionItems actionItems={actionItems} findings={findings ?? []} />

          <ExecutiveAnalysisPanel
            analystSummary={report.analyst_summary}
            managementQuestions={report.management_questions}
            metadata={metadata}
            executiveSummary={report.executive_summary}
            analystOutput={analystOutput}
            verifiedFindings={verifiedFindings}
          />

          <ReportNarrativeEditor
            reportId={report.id}
            executiveSummary={report.executive_summary}
            managementQuestions={report.management_questions ?? []}
          />

          {showAdmin && (
            <EvidencePackEditor evidencePack={report.evidence_pack ?? null} />
          )}

          <div className="grid gap-6 lg:grid-cols-2">
            <PrimaryAnalysisPanel
              primary={contract?.primary_analysis}
              digest={digest}
              coverage={coverage}
              insights={insights.filter(
                (i) =>
                  !contract?.primary_analysis?.triggered_by?.length ||
                  contract.primary_analysis.triggered_by.includes(i.domain)
              )}
            />
            <OrgWideSynthesisPanel
              synthesis={contract?.org_wide_synthesis}
              conditionalInsights={analystOutput?.conditional_insights}
            />
          </div>

          <UnlocksFromUploadPanel unlocks={contract?.unlocks_from_this_upload} />

          <InsightCardsGrid insights={insights} />

          <ReportFindingsList findings={findings ?? []} hasEvidencePack={hasEvidencePack} />

          {orgCoverage && <ImproveAnalysisPanel coverage={orgCoverage} />}
          {weeklyBrief && <WeeklyBriefPanel brief={weeklyBrief} />}
          <OperationsChatPanel reportId={report.id} />
        </>
      )}

      {showAdmin && (
        <>
          <EvidencePackPanel
            evidencePack={report.evidence_pack}
            evidenceSummary={contract?.evidence_summary}
            generatedAt={report.generated_at}
          />
          <ReportAnalysisDebugPanel
            digest={digest}
            coverage={coverage}
            metadata={metadata}
            orgId={report.org_id}
          />
        </>
      )}

      <ReportSections report={report} />
    </div>
  );
}
