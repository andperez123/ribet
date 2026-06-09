import { AgentChip } from "@/features/agents/AgentChip";
import { Card } from "@/components/ui/Card";
import type { AgentRosterEntry } from "@/lib/types/report";

export function AgentIntelligenceRail({
  agents,
  title = "Agent activity",
}: {
  agents?: AgentRosterEntry[];
  title?: string;
}) {
  if (!agents?.length) return null;

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ribet-text">{title}</h2>
        <p className="mt-1 text-sm text-ribet-muted">
          Domain analysis status from the latest report cycle.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {agents.map((agent) => (
          <AgentChip key={agent.agent} agent={agent} />
        ))}
      </div>
    </Card>
  );
}
