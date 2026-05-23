"use client";

import { useMemo, useState } from "react";
import { Card } from "@/components/ui/Card";
import { isHighSeverity, severityRank } from "@/lib/dashboard/utils";
import type { Finding } from "@/lib/types/report";
import { SeverityBadge } from "./SeverityBadge";

type Filter = "all" | "high";

export function FindingsList({ findings }: { findings: Finding[] }) {
  const [filter, setFilter] = useState<Filter>("all");

  const sorted = useMemo(
    () =>
      [...findings].sort(
        (a, b) => severityRank(a.severity) - severityRank(b.severity)
      ),
    [findings]
  );

  const visible =
    filter === "high" ? sorted.filter((f) => isHighSeverity(f.severity)) : sorted;

  return (
    <Card className="p-0">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ribet-border px-6 py-4">
        <h2 className="text-sm font-semibold text-ribet-text">Findings</h2>
        <div className="flex gap-2">
          {(["all", "high"] as const).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                filter === f
                  ? "bg-ribet-green/20 text-ribet-text"
                  : "text-ribet-muted hover:text-ribet-text"
              }`}
            >
              {f === "all" ? "All" : "High+"}
            </button>
          ))}
        </div>
      </div>
      <ul className="divide-y divide-ribet-border/60">
        {visible.length === 0 ? (
          <li className="px-6 py-8 text-sm text-ribet-muted">
            No findings match this filter.
          </li>
        ) : (
          visible.map((f) => (
            <li key={f.id} className="px-6 py-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <p className="font-medium text-ribet-text">{f.title}</p>
                <SeverityBadge severity={f.severity} />
              </div>
              <p className="mt-1 text-sm text-ribet-muted">{f.detail}</p>
              <p className="mt-2 text-xs text-ribet-muted">
                {f.department} · {f.category}
                {f.suggested_action ? ` · ${f.suggested_action}` : ""}
              </p>
            </li>
          ))
        )}
      </ul>
    </Card>
  );
}
