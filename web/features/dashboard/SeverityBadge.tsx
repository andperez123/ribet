import { Badge } from "@/components/ui/Badge";
import type { Severity } from "@/lib/types/report";

function variantFor(severity: Severity | undefined) {
  const s = severity?.toLowerCase();
  if (s === "critical" || s === "high") return "risk" as const;
  if (s === "medium") return "default" as const;
  return "muted" as const;
}

export function SeverityBadge({ severity }: { severity: Severity | undefined }) {
  const label = severity ? severity.charAt(0).toUpperCase() + severity.slice(1) : "Unknown";
  return <Badge variant={variantFor(severity)}>{label}</Badge>;
}
