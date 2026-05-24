import { MetricsDashboard } from "@/features/admin/MetricsDashboard";
import { fetchAdminMetrics } from "@/lib/api/admin-data";

export default async function AdminMetricsPage() {
  let metrics;
  try {
    metrics = await fetchAdminMetrics();
  } catch {
    return (
      <div className="rounded-2xl border border-ribet-border bg-ribet-card p-8 text-center">
        <p className="text-ribet-text">Could not load metrics.</p>
        <p className="mt-2 text-sm text-ribet-muted">
          Ensure ADMIN_API_KEY is set on the web service and matches the API.
        </p>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="rounded-2xl border border-ribet-border bg-ribet-card p-8 text-center">
        <p className="text-ribet-text">Admin metrics not configured.</p>
        <p className="mt-2 text-sm text-ribet-muted">
          Set ADMIN_API_KEY on the web service.
        </p>
      </div>
    );
  }

  return <MetricsDashboard metrics={metrics} />;
}
