import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatDate } from "@/lib/dashboard/utils";
import type { IngestJobRecord } from "@/lib/types/report";

function statusVariant(status: string) {
  if (status === "done") return "success" as const;
  if (status === "error") return "risk" as const;
  return "muted" as const;
}

export function UploadsTable({ jobs }: { jobs: IngestJobRecord[] }) {
  if (!jobs.length) {
    return (
      <Card>
        <p className="text-sm text-rivet-muted">No uploads yet.</p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="border-b border-rivet-border px-6 py-4">
        <h2 className="text-sm font-semibold text-rivet-text">Recent uploads</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-rivet-border text-rivet-muted">
              <th className="px-6 py-3 font-medium">File</th>
              <th className="px-6 py-3 font-medium">Sector</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Uploaded</th>
              <th className="px-6 py-3 font-medium">Report</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr
                key={job.id}
                className="border-b border-rivet-border/60 last:border-0"
              >
                <td className="px-6 py-3 font-medium text-rivet-text">
                  {job.file_name}
                </td>
                <td className="px-6 py-3 capitalize text-rivet-muted">
                  {job.sector ?? "—"}
                </td>
                <td className="px-6 py-3">
                  <Badge variant={statusVariant(job.status)}>{job.status}</Badge>
                </td>
                <td className="px-6 py-3 text-rivet-muted">
                  {formatDate(job.created_at)}
                </td>
                <td className="px-6 py-3">
                  {job.report_id ? (
                    <Link
                      href={`/dashboard/reports/${job.report_id}`}
                      className="font-medium text-rivet-green hover:underline"
                    >
                      View
                    </Link>
                  ) : (
                    <span className="text-rivet-muted">—</span>
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
