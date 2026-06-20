import Link from "next/link";
import { Card } from "@/components/ui/Card";
import type { InsightMetric, InsightTone, MetricKey } from "@/lib/dashboard/insight-metrics";
import type { OrgCoverage } from "@/lib/types/coverage";

const TONE_STYLES: Record<
  InsightTone,
  { card: string; pill: string; pillLabel: string }
> = {
  good: {
    card: "border-ribet-green/30",
    pill: "bg-ribet-green/15 text-ribet-green border-ribet-green/30",
    pillLabel: "Healthy",
  },
  neutral: {
    card: "",
    pill: "bg-ribet-card text-ribet-muted border-ribet-border",
    pillLabel: "Summary",
  },
  watch: {
    card: "border-amber-500/40 bg-amber-500/5",
    pill: "bg-amber-500/15 text-amber-700 border-amber-500/40",
    pillLabel: "Watch",
  },
  alert: {
    card: "border-ribet-risk/50 bg-ribet-risk/5",
    pill: "bg-ribet-risk/15 text-ribet-risk border-ribet-risk/40",
    pillLabel: "Alert",
  },
};

function UploadNudgeFooter({ orgCoverage }: { orgCoverage: OrgCoverage }) {
  const next = orgCoverage.next_upload;
  if (!next) return null;

  return (
    <p className="border-t border-ribet-border pt-4 text-sm text-ribet-muted">
      Upload{" "}
      <span className="font-medium text-ribet-text">{next.label}</span> to reach{" "}
      <span className="font-medium text-ribet-text">
        {next.confidence_if_uploaded}%
      </span>{" "}
      confidence.{" "}
      <Link
        href="/dashboard/upload"
        className="font-medium text-ribet-green hover:opacity-90"
      >
        Upload now →
      </Link>
    </p>
  );
}

export function ExecutiveInsightsBar({
  metrics,
  takeaways,
  title,
  subtitle,
  orgCoverage,
}: {
  metrics: InsightMetric[];
  takeaways?: Partial<Record<MetricKey, string>>;
  title: string;
  subtitle?: string;
  orgCoverage?: OrgCoverage | null;
}) {
  if (!metrics.length) return null;

  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold text-ribet-text">{title}</h2>
        {subtitle && (
          <p className="mt-1 text-sm text-ribet-muted">{subtitle}</p>
        )}
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {metrics.map((item) => {
          const styles = TONE_STYLES[item.tone];
          const takeaway = takeaways?.[item.key];
          const footnote = takeaway ?? item.hint;

          return (
            <Card key={item.key} className={`min-w-0 ${styles.card}`}>
              <div className="flex items-start justify-between gap-2">
                <p
                  className="truncate text-sm text-ribet-muted"
                  title={item.label}
                >
                  {item.label}
                </p>
                {(item.tone === "alert" || item.tone === "watch") && (
                  <span
                    className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${styles.pill}`}
                  >
                    {styles.pillLabel}
                  </span>
                )}
              </div>
              <p className="mt-2 text-xl font-semibold leading-tight tabular-nums text-ribet-text sm:text-2xl">
                {item.value}
              </p>
              {item.context && (
                <p
                  className="mt-1 truncate text-xs text-ribet-muted"
                  title={item.context}
                >
                  {item.context}
                </p>
              )}
              {footnote && (
                <p className="mt-2 text-xs leading-relaxed text-ribet-muted">
                  {footnote}
                </p>
              )}
            </Card>
          );
        })}
      </div>
      {orgCoverage && <UploadNudgeFooter orgCoverage={orgCoverage} />}
    </section>
  );
}
