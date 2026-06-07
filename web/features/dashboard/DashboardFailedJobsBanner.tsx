import Link from "next/link";
import { UploadJobErrorPanel } from "@/features/upload/UploadJobErrorPanel";
import { firstJobError } from "@/lib/upload/job-errors";
import type { IngestJobRecord } from "@/lib/types/report";

export function DashboardFailedJobsBanner({
  jobs,
}: {
  jobs: IngestJobRecord[];
}) {
  const failed = jobs.filter((j) => j.status === "error");
  if (!failed.length) return null;

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-ribet-text">
            Upload{failed.length > 1 ? "s" : ""} need attention
          </h2>
          <p className="mt-1 text-sm text-ribet-muted">
            One or more files could not be processed. Fix the export and re-upload,
            or try CSV if Excel is failing.
          </p>
        </div>
        <Link
          href="/#upload"
          className="text-sm font-medium text-ribet-green hover:underline"
        >
          Upload again →
        </Link>
      </div>
      <div className="space-y-2">
        {failed.slice(0, 5).map((job) => {
          const err = firstJobError(job.errors);
          if (!err) return null;
          return (
            <UploadJobErrorPanel
              key={job.id}
              jobId={job.id}
              fileName={job.file_name}
              error={err}
              intakeMetadata={job.intake_metadata}
            />
          );
        })}
      </div>
    </section>
  );
}
