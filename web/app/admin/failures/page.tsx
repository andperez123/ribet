import { JobFailuresDashboard } from "@/features/admin/JobFailuresDashboard";
import { fetchAdminJobFailures } from "@/lib/api/admin-data";

export default async function AdminJobFailuresPage() {
  let data;
  try {
    data = await fetchAdminJobFailures(100);
  } catch {
    return (
      <div className="rounded-2xl border border-ribet-border bg-ribet-card p-8 text-center">
        <p className="text-ribet-text">Could not load job failures.</p>
        <p className="mt-2 text-sm text-ribet-muted">
          Ensure ADMIN_API_KEY is set on the web service and matches the API.
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-2xl border border-ribet-border bg-ribet-card p-8 text-center">
        <p className="text-ribet-text">Admin job failures not configured.</p>
        <p className="mt-2 text-sm text-ribet-muted">
          Set ADMIN_API_KEY on the web service.
        </p>
      </div>
    );
  }

  return <JobFailuresDashboard data={data} />;
}
