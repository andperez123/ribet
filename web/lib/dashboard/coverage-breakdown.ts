import type { OrgCoverage } from "@/lib/types/coverage";
import type { DataCoverage } from "@/lib/types/report";

const DOMAIN_UPLOADS: Array<{ key: keyof DataCoverage; label: string }> = [
  { key: "ar", label: "AR Aging" },
  { key: "ap", label: "AP Aging" },
  { key: "gl", label: "GL Detail" },
  { key: "inventory", label: "Inventory" },
];

export type CoverageBreakdown = {
  understood: string[];
  missing: string[];
};

export function buildCoverageBreakdown(
  coverage: DataCoverage,
  orgCoverage?: OrgCoverage | null
): CoverageBreakdown {
  const understood: string[] = [];
  const missing: string[] = [];

  for (const item of DOMAIN_UPLOADS) {
    if (coverage[item.key]) {
      understood.push(item.label);
    } else {
      missing.push(item.label);
    }
  }

  if (orgCoverage) {
    for (const item of orgCoverage.understood) {
      if (!understood.includes(item.label)) {
        understood.push(item.label);
      }
    }
    for (const item of orgCoverage.needed) {
      if (item.covered || !item.uploadable) continue;
      if (!missing.includes(item.label) && !understood.includes(item.label)) {
        missing.push(item.label);
      }
    }
  }

  return {
    understood: [...new Set(understood)],
    missing: [...new Set(missing.filter((m) => !understood.includes(m)))],
  };
}
