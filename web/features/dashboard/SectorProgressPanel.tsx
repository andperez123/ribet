import Link from "next/link";
import { Lock, Unlock } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { Finding } from "@/lib/types/report";
import type { OrgProgress } from "@/lib/sectors";

type Props = {
  progress: OrgProgress;
  findings?: Finding[];
};

function sectorInsight(
  capabilityId: string,
  findings: Finding[] | undefined
): string | null {
  if (!findings?.length) return null;
  const financialTypes = ["ar_aging", "ap_aging", "cash_flow", "gl"];
  const operationalTypes = ["inventory", "adjustment"];

  if (capabilityId === "cash_flow_logistics") {
    const hit = findings.find(
      (f) =>
        f.category === "financial" ||
        financialTypes.some((t) => f.finding_type?.includes(t))
    );
    return hit ? hit.title : null;
  }
  if (capabilityId === "inventory_logistics") {
    const hit = findings.find(
      (f) =>
        f.category === "operational" ||
        operationalTypes.some((t) => f.finding_type?.includes(t))
    );
    return hit ? hit.title : null;
  }
  return null;
}

export function SectorProgressPanel({ progress, findings }: Props) {
  const { sectors, capabilities, coverage_count } = progress;

  return (
    <div className="space-y-6">
      <Card>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-ribet-text">
            Data coverage
          </h2>
          <Badge variant="default">
            {coverage_count} of {sectors.length} sectors
          </Badge>
        </div>
        <div className="flex flex-wrap gap-2">
          {sectors.map((sector) => (
            <div
              key={sector.id}
              className={`rounded-lg border px-3 py-2 text-sm ${
                sector.covered
                  ? "border-ribet-green/40 bg-ribet-green/10"
                  : "border-ribet-border bg-ribet-card/50"
              }`}
            >
              <span className="font-medium text-ribet-text">{sector.label}</span>
              {sector.covered ? (
                <span className="ml-2 text-xs text-ribet-muted">
                  {sector.count} file{sector.count === 1 ? "" : "s"}
                </span>
              ) : (
                <span className="ml-2 text-xs text-ribet-muted">Not yet</span>
              )}
            </div>
          ))}
        </div>
        {coverage_count < sectors.length && (
          <p className="mt-4 text-sm text-ribet-muted">
            <Link href="/#upload" className="font-medium text-ribet-green hover:underline">
              Upload more sectors
            </Link>{" "}
            to unlock logistics insights below.
          </p>
        )}
      </Card>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-ribet-text">
          Logistics insights
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {capabilities.map((cap) => {
            const insight = cap.unlocked
              ? sectorInsight(cap.id, findings)
              : null;
            return (
              <Card
                key={cap.id}
                className={
                  cap.unlocked
                    ? "border-ribet-green/30"
                    : "border-ribet-border opacity-90"
                }
              >
                <div className="flex items-start gap-2">
                  {cap.unlocked ? (
                    <Unlock className="mt-0.5 h-4 w-4 shrink-0 text-ribet-green" />
                  ) : (
                    <Lock className="mt-0.5 h-4 w-4 shrink-0 text-ribet-muted" />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-ribet-text">{cap.name}</p>
                    <p className="mt-1 text-xs text-ribet-muted">
                      {cap.description}
                    </p>
                    {cap.unlocked ? (
                      <p className="mt-2 text-sm text-ribet-text">
                        {insight ??
                          "Upload more data in this area to deepen insights."}
                      </p>
                    ) : (
                      <p className="mt-2 text-xs text-ribet-muted">
                        {cap.requirement}
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
