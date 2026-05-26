import { AsyncWorkflowBanner } from "@/components/ui/AsyncWorkflowBanner";
import { asyncWorkflow } from "@/lib/content/asyncWorkflow";
import type { IngestJobRecord } from "@/lib/types/report";

const ACTIVE = new Set(["pending", "processing"]);

export function DashboardProcessingBanner({
  jobs,
  variant = "upload",
}: {
  jobs: IngestJobRecord[];
  variant?: "demo" | "upload";
}) {
  const active = jobs.filter((j) => ACTIVE.has(j.status));
  if (!active.length) return null;

  const copy =
    variant === "demo" ? asyncWorkflow.demo : asyncWorkflow.dashboard;

  return (
    <AsyncWorkflowBanner
      title={copy.title}
      body={copy.body}
      showSpinner
      dashboardHref="/dashboard"
    />
  );
}
