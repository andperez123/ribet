import Link from "next/link";
import { EmptyState } from "@/components/ui/EmptyState";

export default function ReportNotFound() {
  return (
    <EmptyState
      title="Report not found"
      description="This report may have been removed or belongs to another organization."
      actionLabel="Back to dashboard"
      actionHref="/dashboard"
    />
  );
}
