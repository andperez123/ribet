import Link from "next/link";
import { AlertCircle } from "lucide-react";
import type { IngestJobRecord } from "@/lib/types/report";

export function DashboardFailedJobsBanner({
  jobs,
}: {
  jobs: IngestJobRecord[];
}) {
  const failed = jobs.filter((j) => j.status === "error");
  if (!failed.length) return null;

  const succeeded = jobs.filter((j) => j.status === "done").length;

  return (
    <div
      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-ribet-risk/25 bg-ribet-risk/5 px-4 py-3"
      role="alert"
    >
      <div className="flex min-w-0 items-center gap-2.5">
        <AlertCircle className="h-4 w-4 shrink-0 text-ribet-risk" />
        <p className="text-sm text-ribet-text">
          <span className="font-semibold">
            {failed.length} upload{failed.length > 1 ? "s" : ""} failed
          </span>
          {succeeded > 0 && (
            <span className="text-ribet-muted">
              {" "}
              · {succeeded} succeeded
            </span>
          )}
          <span className="text-ribet-muted">
            {" "}
            — fix exports and re-upload, or try CSV if Excel is failing.
          </span>
        </p>
      </div>
      <Link
        href="/dashboard/upload"
        className="shrink-0 text-sm font-medium text-ribet-green hover:underline"
      >
        Manage uploads →
      </Link>
    </div>
  );
}
