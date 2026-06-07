import { getFastApiBase } from "./bff";
import type { AdminJobFailuresResponse } from "@/lib/types/admin";
import type { AdminMetrics } from "@/lib/types/metrics";

export async function fetchAdminMetrics(): Promise<AdminMetrics | null> {
  const adminKey = process.env.ADMIN_API_KEY;
  if (!adminKey) {
    return null;
  }

  const res = await fetch(`${getFastApiBase()}/v1/admin/metrics`, {
    headers: { "X-Admin-Key": adminKey },
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Admin metrics failed: ${res.status}`);
  }

  return res.json() as Promise<AdminMetrics>;
}

export async function fetchAdminJobFailures(
  limit = 50
): Promise<AdminJobFailuresResponse | null> {
  const adminKey = process.env.ADMIN_API_KEY;
  if (!adminKey) {
    return null;
  }

  const res = await fetch(
    `${getFastApiBase()}/v1/admin/job-failures?limit=${limit}`,
    {
      headers: { "X-Admin-Key": adminKey },
      cache: "no-store",
    }
  );

  if (!res.ok) {
    throw new Error(`Admin job failures failed: ${res.status}`);
  }

  return res.json() as Promise<AdminJobFailuresResponse>;
}
