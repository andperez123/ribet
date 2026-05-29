import { OrgResolutionError, getFastApiBase, getProxyHeaders } from "./bff";
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
  try {
    const res = await fetch(`${getFastApiBase()}${path}`, {
      headers: await getProxyHeaders(),
      cache: "no-store",
    });
    if (res.status === 404) return null;
    if (!res.ok) {
      console.error(`[server-data] ${path} → ${res.status}: ${await res.text()}`);
      return null;
    }
    return res.json() as Promise<T>;
  } catch (err) {
    if (err instanceof OrgResolutionError) {
      throw err;
    }
    console.error(
      `[server-data] ${path} → fetch failed (${getFastApiBase()}):`,
      err
    );
    return null;
  }
}

export const serverData = {
  latestReport: () => fetchApi<OperationalReport>("/v1/reports/latest"),
  report: (id: string) => fetchApi<OperationalReport>(`/v1/reports/${id}`),
  reports: (limit = 20) =>
    fetchApi<import("@/lib/types/report").ReportsListResponse>(
      `/v1/reports?limit=${limit}`
    ),
  findings: (limit = 50) =>
    fetchApi<Finding[]>(`/v1/findings?limit=${limit}`),
  healthScore: () => fetchApi<HealthScore>("/v1/health/score"),
  healthHistory: (limit = 12) =>
    fetchApi<HealthHistory>(`/v1/health/history?limit=${limit}`),
  ingestJobs: (limit = 20) =>
    fetchApi<IngestJobsResponse>(`/v1/ingest/jobs?limit=${limit}`),
  weeklyBrief: () => fetchApi<WeeklyBrief>("/v1/brief/weekly"),
  orgProgress: () => fetchApi<OrgProgress>("/v1/org/progress"),
  snapshotsLatest: () =>
    fetchApi<import("@/lib/types/snapshot").OperationalSnapshotOut>(
      "/v1/snapshots/latest"
    ),
  snapshotsHistory: (limit = 12) =>
    fetchApi<import("@/lib/types/snapshot").SnapshotHistoryOut>(
      `/v1/snapshots/history?limit=${limit}`
    ),
};
