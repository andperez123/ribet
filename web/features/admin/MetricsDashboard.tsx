"use client";

import { useMemo, useState } from "react";
import { Card } from "@/components/ui/Card";
import type { AdminMetrics, OrgMetricsRow } from "@/lib/types/metrics";

function KpiCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <Card>
      <p className="text-sm text-ribet-muted">{label}</p>
      <p className="mt-2 text-4xl font-semibold tracking-tight text-ribet-text">
        {value}
      </p>
      {sub && <p className="mt-1 text-xs text-ribet-muted">{sub}</p>}
    </Card>
  );
}

function WeeklyBarChart({
  title,
  data,
  field,
  maxValue,
}: {
  title: string;
  data: AdminMetrics["weekly"];
  field: "uploads" | "reports";
  maxValue: number;
}) {
  return (
    <Card>
      <h3 className="text-sm font-medium text-ribet-text">{title}</h3>
      <div className="mt-4 flex items-end gap-1">
        {data.map((bucket) => {
          const value = bucket[field];
          const height = maxValue > 0 ? (value / maxValue) * 100 : 0;
          return (
            <div
              key={bucket.week_start}
              className="group flex flex-1 flex-col items-center gap-1"
              title={`${bucket.week_start}: ${value}`}
            >
              <div className="relative flex h-32 w-full items-end">
                <div
                  className="w-full rounded-t bg-ribet-green/80"
                  style={{ height: `${Math.max(height, value > 0 ? 4 : 0)}%` }}
                />
              </div>
              <span className="hidden text-[10px] text-ribet-muted sm:block">
                {bucket.week_start.slice(5)}
              </span>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function orgsToCsv(orgs: OrgMetricsRow[]): string {
  const headers = [
    "org_id",
    "name",
    "created_at",
    "uploads",
    "reports",
    "sectors_covered",
    "findings",
    "last_upload_at",
    "last_report_at",
    "health_score",
  ];
  const rows = orgs.map((o) =>
    [
      o.org_id,
      `"${o.name.replace(/"/g, '""')}"`,
      o.created_at,
      o.uploads,
      o.reports,
      o.sectors_covered,
      o.findings,
      o.last_upload_at ?? "",
      o.last_report_at ?? "",
      o.health_score ?? "",
    ].join(",")
  );
  return [headers.join(","), ...rows].join("\n");
}

type SortKey = keyof Pick<
  OrgMetricsRow,
  "name" | "uploads" | "reports" | "findings" | "sectors_covered" | "created_at"
>;

export function MetricsDashboard({ metrics }: { metrics: AdminMetrics }) {
  const [sortKey, setSortKey] = useState<SortKey>("reports");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sortedOrgs = useMemo(() => {
    const copy = [...metrics.orgs];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "string" && typeof bv === "string") {
        return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      const an = Number(av) || 0;
      const bn = Number(bv) || 0;
      return sortDir === "asc" ? an - bn : bn - an;
    });
    return copy;
  }, [metrics.orgs, sortKey, sortDir]);

  const maxUploads = Math.max(...metrics.weekly.map((w) => w.uploads), 1);
  const maxReports = Math.max(...metrics.weekly.map((w) => w.reports), 1);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  function exportCsv() {
    const csv = orgsToCsv(sortedOrgs);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ribet-traction-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const updated = new Date(metrics.generated_at).toLocaleString();

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ribet-text md:text-3xl">
            Traction Metrics
          </h1>
          <p className="mt-1 text-sm text-ribet-muted">
            Product KPIs for investor reporting · Updated {updated}
          </p>
        </div>
        <button
          type="button"
          onClick={exportCsv}
          className="rounded-full border border-ribet-border bg-ribet-card px-5 py-2.5 text-sm font-medium text-ribet-text hover:bg-ribet-bg"
        >
          Export org CSV
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <KpiCard label="Reports generated" value={metrics.totals.reports} />
        <KpiCard label="Files uploaded" value={metrics.totals.uploads} />
        <KpiCard
          label="Active orgs (30d)"
          value={metrics.totals.active_orgs_30d}
          sub={`${metrics.totals.orgs} total orgs`}
        />
        <KpiCard
          label="Activation rate"
          value={`${metrics.activation.rate_pct}%`}
          sub={`${metrics.activation.orgs_with_report} orgs with report`}
        />
        <KpiCard
          label="Time to first report"
          value={
            metrics.activation.median_time_to_first_report_hours != null
              ? `${metrics.activation.median_time_to_first_report_hours}h`
              : "—"
          }
          sub="Median"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KpiCard
          label="Upload success rate"
          value={`${metrics.engagement.upload_success_rate_pct}%`}
        />
        <KpiCard
          label="Report yield rate"
          value={`${metrics.engagement.report_yield_rate_pct}%`}
        />
        <KpiCard
          label="Repeat upload rate"
          value={`${metrics.engagement.repeat_upload_rate_pct}%`}
        />
        <KpiCard
          label="Avg sectors / org"
          value={metrics.engagement.avg_sectors_per_active_org}
        />
        <KpiCard label="Findings delivered" value={metrics.totals.findings} />
        <KpiCard
          label="Avg findings / report"
          value={metrics.engagement.avg_findings_per_report}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <WeeklyBarChart
          title="Uploads per week"
          data={metrics.weekly}
          field="uploads"
          maxValue={maxUploads}
        />
        <WeeklyBarChart
          title="Reports per week"
          data={metrics.weekly}
          field="reports"
          maxValue={maxReports}
        />
      </div>

      <Card className="overflow-x-auto p-0">
        <div className="border-b border-ribet-border px-6 py-4">
          <h3 className="text-sm font-medium text-ribet-text">Per-org breakdown</h3>
        </div>
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="border-b border-ribet-border text-ribet-muted">
              {(
                [
                  ["name", "Organization"],
                  ["uploads", "Uploads"],
                  ["reports", "Reports"],
                  ["sectors_covered", "Sectors"],
                  ["findings", "Findings"],
                  ["created_at", "Created"],
                ] as const
              ).map(([key, label]) => (
                <th key={key} className="px-6 py-3 font-medium">
                  <button
                    type="button"
                    onClick={() => toggleSort(key)}
                    className="hover:text-ribet-text"
                  >
                    {label}
                    {sortKey === key ? (sortDir === "asc" ? " ↑" : " ↓") : ""}
                  </button>
                </th>
              ))}
              <th className="px-6 py-3 font-medium">Health</th>
              <th className="px-6 py-3 font-medium">Last upload</th>
            </tr>
          </thead>
          <tbody>
            {sortedOrgs.map((org) => (
              <tr
                key={org.org_id}
                className="border-b border-ribet-border/60 last:border-0"
              >
                <td className="px-6 py-3 font-medium text-ribet-text">{org.name}</td>
                <td className="px-6 py-3">{org.uploads}</td>
                <td className="px-6 py-3">{org.reports}</td>
                <td className="px-6 py-3">{org.sectors_covered}</td>
                <td className="px-6 py-3">{org.findings}</td>
                <td className="px-6 py-3 text-ribet-muted">
                  {org.created_at
                    ? new Date(org.created_at).toLocaleDateString()
                    : "—"}
                </td>
                <td className="px-6 py-3">
                  {org.health_score != null ? org.health_score : "—"}
                </td>
                <td className="px-6 py-3 text-ribet-muted">
                  {org.last_upload_at
                    ? new Date(org.last_upload_at).toLocaleDateString()
                    : "—"}
                </td>
              </tr>
            ))}
            {sortedOrgs.length === 0 && (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-ribet-muted">
                  No organizations yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
