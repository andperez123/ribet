import type { DataCoverage, DataDigest, OperationalReport } from "@/lib/types/report";

export function coverageFromDomains(domains: string[]): Pick<
  DataCoverage,
  "ar" | "ap" | "gl" | "inventory"
> {
  return {
    ar: domains.includes("ar"),
    ap: domains.includes("ap"),
    gl: domains.includes("gl"),
    inventory: domains.includes("inventory"),
  };
}

/** Prefer org-wide synthesis digest; fall back to per-report digest/coverage. */
export function deriveReportDigestCoverage(
  report: OperationalReport,
  emptyDigest: DataDigest,
  emptyCoverage: DataCoverage
): { digest: DataDigest; coverage: DataCoverage } {
  const contract = report.report_contract;
  const synthesis = contract?.org_wide_synthesis;
  const domains = synthesis?.org_context_domains ?? [];

  const digest = {
    ...emptyDigest,
    ...(synthesis?.digest ?? contract?.digest_kpis ?? report.data_digest ?? {}),
  };

  const baseCoverage = {
    ...emptyCoverage,
    ...(report.data_coverage ?? {}),
  };

  if (domains.length > 0) {
    return {
      digest,
      coverage: {
        ...baseCoverage,
        ...coverageFromDomains(domains),
      },
    };
  }

  return { digest, coverage: baseCoverage };
}
