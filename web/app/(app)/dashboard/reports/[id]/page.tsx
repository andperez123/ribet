import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { AnalystNarrativePanel } from "@/features/dashboard/AnalystNarrativePanel";
import { TopRisksPanel } from "@/features/dashboard/TopRisksPanel";
import { CoverageDeltaBanner } from "@/features/dashboard/CoverageDeltaBanner";
import { DataCoverageBanner } from "@/features/dashboard/DataCoverageBanner";
import { DeleteReportButton } from "@/features/dashboard/DeleteReportButton";
import {
  OrgWideSynthesisPanel,
  PrimaryAnalysisPanel,
} from "@/features/dashboard/ReportAnalysisSections";
import { ReportActionItems } from "@/features/dashboard/ReportActionItems";
import { ReportAnalysisDebugPanel } from "@/features/dashboard/ReportAnalysisDebugPanel";
import { ReportFindingsList } from "@/features/dashboard/ReportFindingsList";
import { ReportSections } from "@/features/dashboard/ReportSections";
import { TopEntitiesPanel } from "@/features/dashboard/TopEntitiesPanel";
import { TopSignalsHero } from "@/features/dashboard/TopSignalsHero";
import { UnlocksFromUploadPanel } from "@/features/dashboard/UnlocksFromUploadPanel";
import { WeeklyBriefPanel } from "@/features/dashboard/WeeklyBriefPanel";
import { HealthScoreHero } from "@/features/dashboard/HealthScoreHero";
import { HealthComponentsGrid } from "@/features/dashboard/HealthComponentsGrid";
import { ConditionalInsightsPanel } from "@/features/dashboard/ConditionalInsightsPanel";
import { serverData } from "@/lib/api/server-data";
import {
  buildTopSignals,
  getActionItems,
  sortDomainInsights,
} from "@/lib/dashboard/report-signals";
import { digestHasData, formatDate, healthStatusColor } from "@/lib/dashboard/utils";
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

const EMPTY_METADATA: AnalysisMetadata = {
  narration: "legacy",
  finding_count: 0,
  narrated_count: 0,
  data_domains_present: [],
};

const showDebugPanel =
  process.env.RIBET_DEBUG === "true" ||
  process.env.NODE_ENV === "development";

export default async function ReportPage({ params }: Props) {
  const { id } = await params;
  const [report, brief, healthScore, findings] = await Promise.all([
    serverData.report(id),
    serverData.weeklyBrief(id),
    serverData.healthScore(),
    serverData.findings(50, id),
  ]);

  if (!report) notFound();

  const contract = report.report_contract;
  const digest = { ...EMPTY_DIGEST, ...(contract?.digest_kpis ?? report.data_digest ?? {}) };
  const coverage = { ...EMPTY_COVERAGE, ...(report.data_coverage ?? {}) };
  const insights: DomainInsight[] = sortDomainInsights(
    contract?.domain_insights ?? report.domain_insights ?? []
  );
  const metadata = report.analysis_metadata ?? EMPTY_METADATA;
  const analystOutput = (report.analyst_output ?? null) as AnalystOutput | null;
  const hasData = digestHasData(digest);
  const topSignals = buildTopSignals(report, findings ?? []);
  const actionItems = getActionItems(report, findings ?? []);

  if (hasData && insights.length === 0) {
    console.error(
      `[report-page] Insight invariant: digest has data but domain_insights is empty (report ${id})`
    );
  }

  return (
    <div className="space-y-8">
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
        <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-ribet-muted">
          <span>Generated {formatDate(report.generated_at)}</span>
          <Badge variant="default">{report.health_score} / 100</Badge>
          <span className={healthStatusColor(report.health_status)}>
            {report.health_status}
          </span>
          <a
            href={`/api/reports/${report.id}/pdf`}
            className="font-medium text-ribet-green hover:underline"
            download
          >
            Download PDF
          </a>
          <DeleteReportButton
            reportId={report.id}
            redirectTo="/dashboard/reports"
          />
        </div>
      </div>

      {healthScore && <HealthScoreHero score={healthScore} />}
      {healthScore && hasData && (
        <HealthComponentsGrid score={healthScore} analystOutput={analystOutput} />
      )}

      <DataCoverageBanner coverage={coverage} digest={digest} />

      {(contract?.coverage_delta || contract?.confidence_score) && (
        <CoverageDeltaBanner
          coverageDelta={contract?.coverage_delta}
          confidenceScore={contract?.confidence_score}
        />
      )}

      {!hasData && (
        <Card className="border-dashed">
          <p className="text-sm text-ribet-muted">
            {report.executive_summary[0] ??
              "Upload AR, AP, GL, or inventory exports to generate operational insights."}
          </p>
          <Link
            href="/#upload"
            className="mt-4 inline-block text-sm font-medium text-ribet-green hover:opacity-90"
          >
            Upload files →
          </Link>
        </Card>
      )}

      {hasData && (
        <>
          <TopSignalsHero signals={topSignals} />
          <TopRisksPanel analystOutput={analystOutput} />
          <ReportActionItems actionItems={actionItems} findings={findings ?? []} />

          <PrimaryAnalysisPanel
            primary={contract?.primary_analysis}
            digest={digest}
            coverage={coverage}
            insights={insights}
          />

          <UnlocksFromUploadPanel unlocks={contract?.unlocks_from_this_upload} />

          <OrgWideSynthesisPanel synthesis={contract?.org_wide_synthesis} />

          <ConditionalInsightsPanel analystOutput={analystOutput} />

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <AnalystNarrativePanel
                analystSummary={report.analyst_summary}
                managementQuestions={report.management_questions}
                metadata={metadata}
                executiveSummary={report.executive_summary}
                analystOutput={analystOutput}
              />
            </div>
            <div>{brief && <WeeklyBriefPanel brief={brief} />}</div>
          </div>

          {(report.improvement_notes?.length ?? 0) > 0 && (
            <Card>
              <h2 className="text-sm font-semibold text-ribet-text">
                Since last upload
              </h2>
              <ul className="mt-3 space-y-2 text-sm text-ribet-muted">
                {report.improvement_notes?.map((note) => (
                  <li key={note.message}>{note.message}</li>
                ))}
              </ul>
            </Card>
          )}

          <TopEntitiesPanel digest={digest} coverage={coverage} />
        </>
      )}

      <ReportFindingsList findings={findings ?? []} />

      {showDebugPanel && (
        <ReportAnalysisDebugPanel
          digest={digest}
          coverage={coverage}
          metadata={metadata}
          orgId={report.org_id}
        />
      )}

      <ReportSections report={report} />
    </div>
  );
}
