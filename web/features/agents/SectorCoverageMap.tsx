import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { AgentRosterEntry } from "@/lib/types/report";
import type { OrgProgress } from "@/lib/sectors";

export function SectorCoverageMap({
  progress,
  agentRoster,
}: {
  progress: OrgProgress;
  agentRoster?: AgentRosterEntry[];
}) {
  const { sectors, coverage_count } = progress;
  const activeAgents =
    agentRoster?.filter((a) => a.status === "complete" || a.status === "running")
      .length ?? 0;
  const totalAgents = agentRoster?.length ?? 6;
  const pct = Math.round((coverage_count / sectors.length) * 100);

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-ribet-text">Sector coverage</h2>
        <Badge variant="default">
          {coverage_count}/{sectors.length} sectors · {activeAgents}/{totalAgents} agents
          active
        </Badge>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-ribet-border/40">
        <div
          className="h-full rounded-full bg-ribet-green transition-all"
          style={{ width: `${pct}%` }}
        />
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
            <span className="ml-2 text-xs text-ribet-muted">
              {sector.covered ? "✓" : "○"}
            </span>
          </div>
        ))}
      </div>
      {coverage_count < sectors.length && (
        <p className="text-sm text-ribet-muted">
          <Link href="/dashboard/upload" className="font-medium text-ribet-green hover:underline">
            Upload more sectors
          </Link>{" "}
          to unlock cross-domain analyses.
        </p>
      )}
    </Card>
  );
}
