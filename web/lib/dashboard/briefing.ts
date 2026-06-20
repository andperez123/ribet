import type { AnalystOutput, DashboardBriefing } from "@/lib/types/report";

/** Prefer cached AI briefing; fall back to executive summary for older reports. */
export function resolveDashboardBriefing(
  analystOutput?: AnalystOutput | null
): DashboardBriefing | null {
  const briefing = analystOutput?.dashboard_briefing;
  if (briefing?.headline?.trim()) {
    return briefing;
  }

  const exec = analystOutput?.executive_summary?.filter(Boolean) ?? [];
  if (!exec.length) return null;

  const topRisk = analystOutput?.top_risks?.[0];
  return {
    headline: exec[0],
    narrative: exec.slice(1, 3).join(" "),
    focus: topRisk?.recommended_action,
    tone:
      topRisk?.impact === "high"
        ? "caution"
        : topRisk?.impact === "medium"
          ? "neutral"
          : "positive",
  };
}
