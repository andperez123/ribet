import Link from "next/link";
import { ReportSetupWorkspace } from "@/features/dashboard/report-setup/ReportSetupWorkspace";
import { getFastApiBase, getProxyHeaders } from "@/lib/api/bff";
import type { ReportSetupResponse } from "@/lib/types/report";

async function loadSetup(): Promise<ReportSetupResponse | null> {
  try {
    const res = await fetch(`${getFastApiBase()}/v1/reports/setup?preview=true`, {
      headers: await getProxyHeaders(),
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json() as Promise<ReportSetupResponse>;
  } catch {
    return null;
  }
}

export default async function ReportSetupPage() {
  const setup = await loadSetup();

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/dashboard/reports"
          className="text-sm font-medium text-ribet-muted hover:text-ribet-text"
        >
          ← Report history
        </Link>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight text-ribet-text md:text-3xl">
          Report Sources &amp; Assumptions
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-ribet-muted">
          Choose which uploads feed your operational health report, add business
          assumptions, preview coverage impact, and regenerate.
        </p>
      </div>

      {setup ? (
        <ReportSetupWorkspace initial={setup} />
      ) : (
        <p className="text-sm text-ribet-muted">Unable to load report setup.</p>
      )}
    </div>
  );
}
