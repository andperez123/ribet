import { Lock, Loader2 } from "lucide-react";
import type { AgentRosterEntry } from "@/lib/types/report";

const STATUS_STYLES: Record<
  AgentRosterEntry["status"],
  { dot: string; border: string; label: string }
> = {
  running: {
    dot: "bg-ribet-green animate-pulse",
    border: "border-ribet-green/50",
    label: "Running",
  },
  complete: {
    dot: "bg-ribet-green",
    border: "border-ribet-green/30",
    label: "Done",
  },
  needs_data: {
    dot: "bg-amber-400",
    border: "border-dashed border-amber-500/50",
    label: "Needs data",
  },
  locked: {
    dot: "bg-ribet-muted/40",
    border: "border-ribet-border/60 opacity-80",
    label: "Locked",
  },
};

export function AgentChip({ agent }: { agent: AgentRosterEntry }) {
  const style = STATUS_STYLES[agent.status];

  return (
    <div
      className={`rounded-xl border bg-ribet-card/60 px-3 py-3 ${style.border}`}
    >
      <div className="flex items-start gap-2">
        {agent.status === "running" ? (
          <Loader2 className="mt-0.5 h-3 w-3 shrink-0 animate-spin text-ribet-green" />
        ) : agent.status === "locked" ? (
          <Lock className="mt-0.5 h-3 w-3 shrink-0 text-ribet-muted" />
        ) : (
          <span
            className={`mt-1 h-2 w-2 shrink-0 rounded-full ${style.dot}`}
            aria-hidden
          />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium capitalize text-ribet-text">
              {agent.agent.replace(/_/g, " ")}
            </p>
            <span className="text-[10px] uppercase tracking-wide text-ribet-muted">
              {style.label}
            </span>
          </div>
          <p className="text-xs text-ribet-muted">{agent.domain_scope}</p>
          <p className="mt-1 text-xs text-ribet-text">{agent.status_message}</p>
          {agent.last_completed_at && (
            <p className="mt-1 text-[10px] text-ribet-muted">
              Last run{" "}
              {new Date(agent.last_completed_at).toLocaleString(undefined, {
                dateStyle: "short",
                timeStyle: "short",
              })}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
