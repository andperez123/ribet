import Link from "next/link";
import { ArrowUpRight, FileText, TrendingDown, TrendingUp } from "lucide-react";
import { AreaTrend, RadialGauge, scoreColor, type TrendPoint } from "@/components/charts";
import { Card } from "@/components/ui/Card";
import { DataDigestKpiGrid } from "@/features/dashboard/DataDigestKpiGrid";
import { DeleteReportButton } from "@/features/dashboard/DeleteReportButton";
import { OperationsChatPanel } from "@/features/dashboard/OperationsChatPanel";
import { TryDemoButton } from "@/features/demo/TryDemoButton";
import { serverData } from "@/lib/api/server-data";
import { digestHasData, formatDate, healthStatusColor } from "@/lib/dashboard/utils";
import type {
  DataCoverage,
  DataDigest,
  ReportListItem,
} from "@/lib/types/report";

function shortDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

function StatTile({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: React.ReactNode;
  accent?: string;
}) {
  return (
    <Card variant="stat" className="min-w-0">
      <p className="truncate text-[10px] font-medium uppercase tracking-wide text-ribet-muted">
        {label}
      </p>
      <p
        className="mt-1 text-2xl font-semibold leading-tight tabular-nums"
        style={accent ? { color: accent } : undefined}
      >
        {value}
      </p>
      {sub && <div className="mt-0.5 text-xs text-ribet-muted">{sub}</div>}
    </Card>
  );
}

function ScoreChip({ score }: { score: number }) {
  const color = scoreColor(score);
  return (
    <span
      className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold tabular-nums"
      style={{
        color,
        backgroundColor: `${color}1f`,
        boxShadow: `inset 0 0 0 1.5px ${color}`,
      }}
    >
      {score}
    </span>
  );
}

export default async function ReportsIndexPage() {
  const [data, latest, healthHistory] = await Promise.all([
    serverData.reports(50),
    serverData.latestReport(),
    serverData.healthHistory(12),
  ]);

  const reports: ReportListItem[] = data?.reports ?? [];

  if (reports.length === 0) {
    return (
      <div className="space-y-8">
        <header>
          <Link
            href="/dashboard"
            className="text-sm font-medium text-ribet-muted hover:text-ribet-text"
          >
            ← Dashboard
          </Link>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight text-ribet-text md:text-3xl">
            Reports
          </h1>
        </header>
        <Card className="py-12 text-center">
          <p className="text-lg font-medium text-ribet-text">No reports yet</p>
          <p className="mt-2 text-sm text-ribet-muted">
            Try demo data or upload ERP exports to generate your first report.
          </p>
          <div className="mt-6 flex justify-center gap-4">
            <TryDemoButton />
            <Link
              href="/dashboard/upload"
              className="rounded-full border border-ribet-border px-5 py-2.5 text-sm font-medium text-ribet-text hover:bg-ribet-card"
            >
              Upload files
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  const byNewest = [...reports].sort(
    (a, b) =>
      new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime()
  );
  const latestItem = byNewest[0];
  const previousItem = byNewest[1];

  const scores = byNewest.map((r) => r.health_score);
  const avgScore = Math.round(
    scores.reduce((sum, s) => sum + s, 0) / scores.length
  );
  const totalFindings = byNewest.reduce((sum, r) => sum + r.finding_count, 0);
  const scoreDelta =
    previousItem != null
      ? latestItem.health_score - previousItem.health_score
      : null;

  // Chronological trend for the area chart (oldest → newest).
  const trendSource =
    healthHistory?.snapshots && healthHistory.snapshots.length > 1
      ? healthHistory.snapshots.map((s) => ({
          label: s.computed_at ? shortDate(s.computed_at) : "",
          value: s.score,
          status: s.status,
        }))
      : [...byNewest].reverse().map((r) => ({
          label: shortDate(r.generated_at),
          value: r.health_score,
          status: r.health_status,
        }));
  const trendData: TrendPoint[] = trendSource;

  // Latest report key metrics (best-effort: contract digest → data_digest).
  const digest =
    (latest?.report_contract?.digest_kpis ?? latest?.data_digest ?? null) as
      | DataDigest
      | null;
  const coverage = (latest?.data_coverage ?? null) as DataCoverage | null;
  const showLatestMetrics =
    !!digest && !!coverage && digestHasData(digest);

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Link
            href="/dashboard"
            className="text-sm font-medium text-ribet-muted hover:text-ribet-text"
          >
            ← Dashboard
          </Link>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight text-ribet-text md:text-3xl">
            Reports
          </h1>
          <p className="mt-1 text-sm text-ribet-muted">
            {reports.length} report{reports.length === 1 ? "" : "s"} from your
            uploads — health trajectory, key metrics, and answers on demand.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/dashboard/reports/setup"
            className="rounded-full border border-ribet-border px-5 py-2.5 text-sm font-medium text-ribet-text hover:bg-ribet-card"
          >
            New report
          </Link>
          <Link
            href="/dashboard/upload"
            className="rounded-full bg-ribet-green px-5 py-2.5 text-sm font-medium text-ribet-text hover:opacity-90"
          >
            Upload data
          </Link>
        </div>
      </header>

      {/* Summary numbers */}
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Latest health"
          value={`${latestItem.health_score}`}
          accent={scoreColor(latestItem.health_score)}
          sub={
            <span className={healthStatusColor(latestItem.health_status)}>
              {latestItem.health_status}
            </span>
          }
        />
        <StatTile
          label="Change vs prior"
          value={
            scoreDelta === null
              ? "—"
              : `${scoreDelta > 0 ? "+" : ""}${scoreDelta}`
          }
          sub={
            scoreDelta === null ? (
              "First report"
            ) : scoreDelta === 0 ? (
              "No change"
            ) : (
              <span
                className={`inline-flex items-center gap-1 ${
                  scoreDelta > 0 ? "text-ribet-green" : "text-ribet-risk"
                }`}
              >
                {scoreDelta > 0 ? (
                  <TrendingUp className="h-3.5 w-3.5" />
                ) : (
                  <TrendingDown className="h-3.5 w-3.5" />
                )}
                points since last report
              </span>
            )
          }
        />
        <StatTile
          label="Average health"
          value={`${avgScore}`}
          sub={`across ${reports.length} report${reports.length === 1 ? "" : "s"}`}
        />
        <StatTile
          label="Open findings"
          value={latestItem.finding_count.toLocaleString()}
          sub={`${totalFindings.toLocaleString()} total across history`}
        />
      </section>

      {/* Trajectory + latest score */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-ribet-text">
                Health trajectory
              </h2>
              <p className="mt-1 text-sm text-ribet-muted">
                Operational health score over time (0–100).
              </p>
            </div>
            <span className="text-xs text-ribet-muted">
              {trendData.length} point{trendData.length === 1 ? "" : "s"}
            </span>
          </div>
          <div className="mt-4">
            {trendData.length > 1 ? (
              <AreaTrend data={trendData} height={180} />
            ) : (
              <p className="py-12 text-center text-sm text-ribet-muted">
                Generate another report to see your health trend.
              </p>
            )}
          </div>
        </Card>

        <Card className="flex flex-col items-center justify-center text-center">
          <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Most recent report
          </p>
          <div className="mt-3">
            <RadialGauge
              value={latestItem.health_score}
              label="Health"
              sublabel={latestItem.health_status}
              size={132}
            />
          </div>
          <p className="mt-3 text-xs text-ribet-muted">
            {formatDate(latestItem.generated_at)}
          </p>
          <Link
            href={`/dashboard/reports/${latestItem.id}`}
            className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-ribet-green hover:underline"
          >
            Open full report
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </Card>
      </div>

      {/* Latest report key metrics */}
      {showLatestMetrics && digest && coverage && (
        <section className="space-y-3">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <h2 className="text-lg font-semibold text-ribet-text">
              Latest report at a glance
            </h2>
            <Link
              href={`/dashboard/reports/${latestItem.id}`}
              className="text-sm font-medium text-ribet-green hover:underline"
            >
              See full breakdown →
            </Link>
          </div>
          <DataDigestKpiGrid digest={digest} coverage={coverage} />
        </section>
      )}

      {/* Report history */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-ribet-text">
          Report history
        </h2>
        <Card className="overflow-hidden p-0">
          <ul className="divide-y divide-ribet-border/60">
            {byNewest.map((r) => (
              <li
                key={r.id}
                className="flex flex-wrap items-center gap-4 px-5 py-4 hover:bg-ribet-bg/50"
              >
                <ScoreChip score={r.health_score} />
                <div className="min-w-0 flex-1">
                  <Link
                    href={`/dashboard/reports/${r.id}`}
                    className="block truncate text-sm font-medium text-ribet-text hover:text-ribet-green"
                  >
                    {formatDate(r.generated_at)}
                  </Link>
                  <p className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-ribet-muted">
                    <span className={healthStatusColor(r.health_status)}>
                      {r.health_status}
                    </span>
                    <span aria-hidden>·</span>
                    <span className="inline-flex items-center gap-1">
                      <FileText className="h-3 w-3" />
                      {r.finding_count} finding
                      {r.finding_count === 1 ? "" : "s"}
                    </span>
                  </p>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <Link
                    href={`/dashboard/reports/${r.id}`}
                    className="font-medium text-ribet-green hover:underline"
                  >
                    View
                  </Link>
                  <a
                    href={`/api/reports/${r.id}/pdf`}
                    className="font-medium text-ribet-muted hover:text-ribet-text"
                    download
                  >
                    PDF
                  </a>
                  <DeleteReportButton reportId={r.id} />
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </section>

      {/* Ask the data */}
      <OperationsChatPanel
        reportId={latest?.id ?? latestItem.id}
        title="Ask about your reports"
        subtitle="Get plain-English answers pulled straight from your report data — trends, drivers, and what to do next."
        placeholder="e.g. Why did our health score change this period?"
        suggestions={[
          "What changed since our last report?",
          "Which findings are hurting our health score most?",
          "What should we prioritize this week?",
        ]}
      />
    </div>
  );
}
