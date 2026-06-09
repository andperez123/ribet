import Link from "next/link";
import { Card } from "@/components/ui/Card";
import type { AgentRosterEntry, BlockedAnalysis } from "@/lib/types/report";

export function AgentsWaitingPanel({
  agents,
  blockedAnalyses,
}: {
  agents?: AgentRosterEntry[];
  blockedAnalyses?: BlockedAnalysis[];
}) {
  const waitingAgents =
    agents?.filter((a) => a.status === "needs_data" || a.status === "locked") ?? [];
  const blocked = blockedAnalyses ?? [];

  if (!waitingAgents.length && !blocked.length) return null;

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ribet-text">Agents waiting for data</h2>
        <p className="mt-1 text-sm text-ribet-muted">
          Upload the listed exports to activate blocked analyses.
        </p>
      </div>
      {waitingAgents.length > 0 && (
        <ul className="space-y-2">
          {waitingAgents.map((agent) => (
            <li
              key={agent.agent}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-ribet-border/60 px-3 py-2 text-sm"
            >
              <span className="font-medium capitalize text-ribet-text">
                {agent.agent.replace(/_/g, " ")} Agent
              </span>
              <span className="text-ribet-muted">{agent.status_message}</span>
            </li>
          ))}
        </ul>
      )}
      {blocked.slice(0, 3).map((b) => (
        <div
          key={b.analysis_name}
          className="rounded-lg border border-dashed border-ribet-border px-3 py-2 text-sm"
        >
          <p className="font-medium text-ribet-text">{b.analysis_name}</p>
          <p className="text-ribet-muted">
            Requires {b.requires_uploads.join(", ")}
          </p>
        </div>
      ))}
      <Link
        href="/dashboard/upload"
        className="inline-block text-sm font-medium text-ribet-green hover:underline"
      >
        Upload files →
      </Link>
    </Card>
  );
}
