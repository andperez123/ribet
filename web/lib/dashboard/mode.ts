import type { OrgCoverage } from "@/lib/types/coverage";
import type {
  DataDigest,
  IngestJobRecord,
  OperationalReport,
} from "@/lib/types/report";
import { digestHasData } from "@/lib/dashboard/utils";

export type DashboardMode =
  | "empty"
  | "processing"
  | "data_no_report"
  | "report";

export function getDashboardMode({
  report,
  jobs,
  orgCoverage,
  digest,
}: {
  report: OperationalReport | null;
  jobs: IngestJobRecord[];
  orgCoverage: OrgCoverage | null;
  digest?: DataDigest;
}): DashboardMode {
  const hasActiveJobs = jobs.some(
    (j) => j.status === "pending" || j.status === "processing"
  );
  const hasDoneJobs = jobs.some((j) => j.status === "done");
  const hasCoverage =
    (orgCoverage?.understood?.length ?? 0) > 0 || digestHasData(digest);

  if (report) return "report";
  if (hasActiveJobs) return "processing";
  if (hasDoneJobs || hasCoverage) return "data_no_report";
  return "empty";
}

export function jobSummary(jobs: IngestJobRecord[]) {
  return {
    failed: jobs.filter((j) => j.status === "error").length,
    done: jobs.filter((j) => j.status === "done").length,
    active: jobs.filter(
      (j) => j.status === "pending" || j.status === "processing"
    ).length,
    needsReview: jobs.filter((j) => j.status === "needs_review").length,
  };
}
