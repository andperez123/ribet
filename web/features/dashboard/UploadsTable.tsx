import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatDate } from "@/lib/dashboard/utils";
import type { IngestJobRecord } from "@/lib/types/report";

function statusVariant(status: string) {
  if (status === "done") return "success" as const;
  if (status === "error") return "risk" as const;
  if (status === "needs_review") return "muted" as const;
  return "muted" as const;
}

export function UploadsTable({
  jobs,
  limit,
  showViewAll = false,
}: {
  jobs: IngestJobRecord[];
  limit?: number;
  showViewAll?: boolean;
}) {
  const displayJobs = limit ? jobs.slice(0, limit) : jobs;

  if (!jobs.length) {
    return (
      <Card>
        <p className="text-sm text-ribet-muted">No uploads yet.</p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="flex items-center justify-between border-b border-ribet-border px-6 py-4">
        <h2 className="text-sm font-semibold text-ribet-text">Recent uploads</h2>
        {showViewAll && jobs.length > (limit ?? jobs.length) && (
          <Link
            href="/dashboard/upload"
            className="text-xs font-medium text-ribet-green hover:underline"
          >
            View all →
          </Link>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-ribet-border text-ribet-muted">
              <th className="px-6 py-3 font-medium">File</th>
              <th className="px-6 py-3 font-medium">Sector</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Uploaded</th>
              <th className="px-6 py-3 font-medium">Report</th>
            </tr>
          </thead>
          <tbody>
            {displayJobs.map((job) => (
              <tr
                key={job.id}
                className="border-b border-ribet-border/60 last:border-0"
              >
                <td className="max-w-[200px] truncate px-6 py-3 font-medium text-ribet-text">
                  {job.file_name}
                </td>
                <td className="px-6 py-3 capitalize text-ribet-muted">
                  {job.sector ?? "—"}
                </td>
                <td className="px-6 py-3">
                  <Badge variant={statusVariant(job.status)}>{job.status}</Badge>
                </td>
                <td className="px-6 py-3 text-ribet-muted">
                  {formatDate(job.created_at)}
                </td>
                <td className="px-6 py-3">
                  {job.report_id ? (
                    <Link
                      href={`/dashboard/reports/${job.report_id}`}
                      className="font-medium text-ribet-green hover:underline"
                    >
                      View
                    </Link>
                  ) : job.status === "error" ? (
                    <Link
                      href="/dashboard/upload"
                      className="font-medium text-ribet-green hover:underline"
                    >
                      Re-upload
                    </Link>
                  ) : (
                    <span className="text-ribet-muted">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
