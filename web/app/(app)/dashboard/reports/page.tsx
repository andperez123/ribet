import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { DeleteReportButton } from "@/features/dashboard/DeleteReportButton";
import { TryDemoButton } from "@/features/demo/TryDemoButton";
import { formatDate, healthStatusColor } from "@/lib/dashboard/utils";
import { serverData } from "@/lib/api/server-data";

export default async function ReportsIndexPage() {
  const data = await serverData.reports(50);
  const reports = data?.reports ?? [];

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Link
            href="/dashboard"
            className="text-sm font-medium text-ribet-muted hover:text-ribet-text"
          >
            ← Dashboard
          </Link>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight text-ribet-text md:text-3xl">
            Report history
          </h1>
          <p className="mt-1 text-sm text-ribet-muted">
            Operational health reports generated from your uploads.
          </p>
        </div>
      </div>

      {reports.length === 0 ? (
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
      ) : (
        <Card className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-ribet-border text-ribet-muted">
                  <th className="px-6 py-3 font-medium">Generated</th>
                  <th className="px-6 py-3 font-medium">Score</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium">Findings</th>
                  <th className="px-6 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((r) => (
                  <tr
                    key={r.id}
                    className="border-b border-ribet-border/60 last:border-0"
                  >
                    <td className="px-6 py-3 text-ribet-text">
                      {formatDate(r.generated_at)}
                    </td>
                    <td className="px-6 py-3 font-medium">{r.health_score}</td>
                    <td className="px-6 py-3">
                      <span className={healthStatusColor(r.health_status)}>
                        {r.health_status}
                      </span>
                    </td>
                    <td className="px-6 py-3">{r.finding_count}</td>
                    <td className="px-6 py-3">
                      <div className="flex flex-wrap gap-3">
                        <Link
                          href={`/dashboard/reports/${r.id}`}
                          className="font-medium text-ribet-green hover:underline"
                        >
                          View
                        </Link>
                        <Link
                          href="/dashboard/reports/setup"
                          className="font-medium text-ribet-muted hover:text-ribet-text"
                        >
                          Setup
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
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
