import { getFastApiBase, getProxyHeaders } from "./bff";
import type { OrgProgress } from "@/lib/sectors";
import type {
  Finding,
  HealthHistory,
  HealthScore,
  IngestJobsResponse,
  OperationalReport,
  WeeklyBrief,
} from "@/lib/types/report";

async function fetchApi<T>(path: string): Promise<T | null> {
  const res = await fetch(`${getFastApiBase()}${path}`, {
    headers: getProxyHeaders(),
    cache: "no-store",
  });
  if (res.status === 404) return null;
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

export const serverData = {
  latestReport: () => fetchApi<OperationalReport>("/v1/reports/latest"),
  report: (id: string) => fetchApi<OperationalReport>(`/v1/reports/${id}`),
  findings: (limit = 50) =>
    fetchApi<Finding[]>(`/v1/findings?limit=${limit}`),
  healthScore: () => fetchApi<HealthScore>("/v1/health/score"),
  healthHistory: (limit = 12) =>
    fetchApi<HealthHistory>(`/v1/health/history?limit=${limit}`),
  ingestJobs: (limit = 20) =>
    fetchApi<IngestJobsResponse>(`/v1/ingest/jobs?limit=${limit}`),
  weeklyBrief: () => fetchApi<WeeklyBrief>("/v1/brief/weekly"),
  orgProgress: () => fetchApi<OrgProgress>("/v1/org/progress"),
};
