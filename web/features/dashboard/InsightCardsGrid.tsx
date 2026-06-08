"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { sortDomainInsights } from "@/lib/dashboard/report-signals";
import { INSIGHT_SEVERITY_STYLES } from "@/lib/dashboard/utils";
import type { DomainInsight } from "@/lib/types/report";

function severityLabel(severity: DomainInsight["severity"]): string {
  if (severity === "alert") return "Needs attention";
  if (severity === "watch") return "Monitor";
  return "Insight";
}

function InsightCard({ insight }: { insight: DomainInsight }) {
  const isAlert = insight.severity === "alert";
  return (
    <Card
      className={`border ${INSIGHT_SEVERITY_STYLES[insight.severity]} ${
        isAlert ? "border-l-4 border-l-ribet-risk" : ""
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
          {insight.domain}
        </p>
        <span
          className={`text-xs ${
            isAlert ? "font-semibold text-ribet-risk" : "text-ribet-muted"
          }`}
        >
          {severityLabel(insight.severity)}
        </span>
      </div>
      <p className="mt-2 font-medium text-ribet-text">{insight.title}</p>
      <p className="mt-1 text-sm text-ribet-muted">{insight.body}</p>
      {insight.metric_label && insight.metric_value && (
        <p className="mt-3 text-xs text-ribet-muted">
          {insight.metric_label}:{" "}
          <span className="font-medium text-ribet-text">
            {insight.metric_value}
          </span>
        </p>
      )}
      {insight.source_label && (
        <p className="mt-3 text-xs text-ribet-muted">{insight.source_label}</p>
      )}
    </Card>
  );
}

export function InsightCardsGrid({ insights }: { insights: DomainInsight[] }) {
  const [showDetails, setShowDetails] = useState(false);

  if (!insights.length) return null;

  const sorted = sortDomainInsights(insights);
  const priority = sorted.filter((i) => i.severity !== "info");
  const details = sorted.filter((i) => i.severity === "info");

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold text-ribet-text">Insights</h2>
      {priority.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {priority.map((insight, i) => (
            <InsightCard
              key={`${insight.domain}-${insight.title}-${i}`}
              insight={insight}
            />
          ))}
        </div>
      )}
      {details.length > 0 && (
        <div>
          <button
            type="button"
            onClick={() => setShowDetails((v) => !v)}
            className="text-sm font-medium text-ribet-green hover:opacity-90"
          >
            {showDetails ? "Hide" : "Show"} {details.length} additional detail
            {details.length === 1 ? "" : "s"}
          </button>
          {showDetails && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              {details.map((insight, i) => (
                <InsightCard
                  key={`detail-${insight.domain}-${insight.title}-${i}`}
                  insight={insight}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
