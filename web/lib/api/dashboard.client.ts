import { apiFetch } from "./client";
import { BFF } from "./endpoints";
import type {
  Finding,
  HealthHistory,
  HealthScore,
  IngestJobsResponse,
  OperationalReport,
  WeeklyBrief,
} from "@/lib/types/report";

export const dashboardClient = {
  latestReport: () => apiFetch<OperationalReport>(BFF.reports.latest),
  report: (id: string) => apiFetch<OperationalReport>(BFF.reports.byId(id)),
  findings: (limit = 50) =>
    apiFetch<Finding[]>(BFF.findings, { params: { limit: String(limit) } }),
  healthScore: () => apiFetch<HealthScore>(BFF.healthScore),
  healthHistory: (limit = 12) =>
    apiFetch<HealthHistory>(BFF.healthHistory, {
      params: { limit: String(limit) },
    }),
  ingestJobs: (limit = 20) =>
    apiFetch<IngestJobsResponse>(BFF.ingest.jobs, {
      params: { limit: String(limit) },
    }),
  weeklyBrief: () => apiFetch<WeeklyBrief>(BFF.briefWeekly),
};
