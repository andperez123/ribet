import { Card } from "@/components/ui/Card";
import type { DashboardBriefing } from "@/lib/types/report";

const TONE_CLASSES: Record<
  NonNullable<DashboardBriefing["tone"]>,
  string
> = {
  positive: "border-ribet-green/40 bg-ribet-green/5",
  neutral: "border-ribet-border",
  caution: "border-amber-500/40 bg-amber-500/5",
  critical: "border-ribet-risk/50 bg-ribet-risk/5",
};

export function DashboardBriefingPanel({
  briefing,
  source,
}: {
  briefing?: DashboardBriefing | null;
  source?: string | null;
}) {
  if (!briefing?.headline?.trim()) return null;

  const tone = briefing.tone ?? "neutral";
  const isAi = source === "ai";

  return (
    <Card className={`${TONE_CLASSES[tone]} space-y-4`}>
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ribet-green">
          Intelligence briefing
        </p>
        <span className="rounded-full border border-ribet-border bg-ribet-bg px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-ribet-muted">
          {isAi ? "AI · grounded in your data" : "Verified summary"}
        </span>
      </div>
      <h2 className="text-xl font-semibold leading-snug text-ribet-text md:text-2xl">
        {briefing.headline}
      </h2>
      {briefing.narrative && (
        <p className="max-w-3xl text-sm leading-relaxed text-ribet-muted">
          {briefing.narrative}
        </p>
      )}
      {briefing.focus && (
        <p className="text-sm font-medium text-ribet-text">
          <span className="text-ribet-green">Focus this week: </span>
          {briefing.focus}
        </p>
      )}
    </Card>
  );
}
