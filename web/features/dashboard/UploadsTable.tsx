import Link from "next/link";
import { Fragment } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { UploadJobErrorPanel } from "@/features/upload/UploadJobErrorPanel";
import { formatDate } from "@/lib/dashboard/utils";
import { firstJobError } from "@/lib/upload/job-errors";
import type { IngestJobRecord } from "@/lib/types/report";

function statusVariant(status: string) {
  if (status === "done") return "success" as const;
  if (status === "error") return "risk" as const;
  if (status === "needs_review") return "muted" as const;
  return "muted" as const;
}

export function UploadsTable({ jobs }: { jobs: IngestJobRecord[] }) {
  if (!jobs.length) {
    return (
      <Card>
        <p className="text-sm text-ribet-muted">No uploads yet.</p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="border-b border-ribet-border px-6 py-4">
        <h2 className="text-sm font-semibold text-ribet-text">Recent uploads</h2>
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
            {jobs.map((job) => {
              const err = firstJobError(job.errors);
              return (
                <Fragment key={job.id}>
                  <tr className="border-b border-ribet-border/60 last:border-0">
                    <td className="px-6 py-3 font-medium text-ribet-text">
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
                  {job.status === "error" && err && (
                    <tr className="border-b border-ribet-border/60">
                      <td colSpan={5} className="px-6 pb-4 pt-0">
                        <UploadJobErrorPanel
                          jobId={job.id}
                          error={err}
                          intakeMetadata={job.intake_metadata}
                          compact
                        />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
