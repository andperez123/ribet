import Link from "next/link";
import { Lock, Upload } from "lucide-react";
import { SegmentBar } from "@/components/charts";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { OrgCoverage } from "@/lib/types/coverage";
import type { AnalystOutput, ReportUnlock } from "@/lib/types/report";

const SECTOR_UPLOAD: Record<string, string> = {
  financials: "/dashboard/upload",
  manufacturing: "/dashboard/upload",
  orders: "/dashboard/upload",
  sales: "/dashboard/upload",
};

function LockedPanel({
  label,
  teaser,
  sector,
}: {
  label: string;
  teaser: string;
  sector?: string;
}) {
  return (
    <Card variant="locked" className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-locked-frost" />
      <div className="relative flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Lock className="h-4 w-4 text-ribet-muted" />
          <span className="text-sm font-semibold text-ribet-text">{label}</span>
          <Badge variant="muted">Locked</Badge>
        </div>
        <div className="h-16 rounded-lg bg-gradient-to-r from-ribet-border/40 via-ribet-border/20 to-ribet-border/40 blur-[1px]" />
        <p className="text-sm leading-relaxed text-ribet-muted">{teaser}</p>
        <Link
          href={SECTOR_UPLOAD[sector ?? "financials"] ?? "/dashboard/upload"}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-ribet-green hover:underline"
        >
          <Upload className="h-3.5 w-3.5" />
          Upload to unlock
        </Link>
      </div>
    </Card>
  );
}

function UnlockBanner({ unlocks }: { unlocks: ReportUnlock[] }) {
  if (!unlocks.length) return null;
  return (
    <div className="rounded-xl border border-ribet-green/30 bg-ribet-green/10 px-4 py-3">
      <p className="text-sm font-medium text-ribet-text">Newly unlocked</p>
      <ul className="mt-2 space-y-1">
        {unlocks.map((u, i) => (
          <li key={i} className="text-sm text-ribet-muted">
            ✓ {u.message}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function UnlockRail({
  coverage,
  analystOutput,
  unlocks,
}: {
  coverage: OrgCoverage;
  analystOutput?: AnalystOutput | null;
  unlocks?: ReportUnlock[] | null;
}) {
  const { understood, needed, confidence_breakdown, next_upload } = coverage;
  const conditional = analystOutput?.conditional_insights ?? [];
  const recommended = analystOutput?.recommended_uploads ?? [];
  const uploadableNeeded = needed.filter((n) => n.uploadable);

  const segments = confidence_breakdown.map((b) => ({
    key: b.key,
    label: b.label,
    weight: b.weight,
    covered: b.covered,
    highlighted: next_upload?.key === b.key,
  }));

  const teaserFor = (key: string, label: string) => {
    const cond = conditional.find(
      (c) =>
        c.requires_upload.toLowerCase().includes(label.toLowerCase()) ||
        c.locked_capability.toLowerCase().includes(key)
    );
    if (cond) return cond.insight;
    const rec = recommended.find((r) =>
      r.upload.toLowerCase().includes(label.toLowerCase())
    );
    if (rec) return rec.rationale;
    return `Upload ${label} to unlock cross-domain analysis and raise confidence.`;
  };

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ribet-text">
            Complete the picture
          </h2>
          <p className="mt-1 text-sm text-ribet-muted">
            Every upload unlocks deeper analysis. Here is what Ribet needs next.
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-wide text-ribet-muted">
            Analysis confidence
          </p>
          <p className="text-3xl font-semibold tabular-nums text-ribet-text">
            {coverage.analysis_confidence}%
          </p>
        </div>
      </div>

      {unlocks && unlocks.length > 0 && <UnlockBanner unlocks={unlocks} />}

      {next_upload && (
        <div className="rounded-xl border border-ribet-green/30 bg-ribet-green/10 px-4 py-3 text-sm text-ribet-text">
          Upload{" "}
          <span className="font-semibold">{next_upload.label}</span> to reach{" "}
          <span className="font-semibold tabular-nums">
            {next_upload.confidence_if_uploaded}%
          </span>{" "}
          confidence.
          <Link
            href="/dashboard/upload"
            className="ml-2 font-medium text-ribet-green hover:underline"
          >
            Upload now →
          </Link>
        </div>
      )}

      {segments.length > 0 && (
        <Card>
          <p className="mb-3 text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Confidence ladder
          </p>
          <SegmentBar segments={segments} />
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Ribet understands
          </p>
          <ul className="mt-3 space-y-2">
            {understood.map((item) => (
              <li
                key={item.key}
                className="flex items-center gap-2 text-sm text-ribet-text"
              >
                <span className="text-ribet-green">✓</span>
                {item.label}
              </li>
            ))}
            {!understood.length && (
              <li className="text-sm text-ribet-muted">Nothing yet — upload to start.</li>
            )}
          </ul>
        </Card>

        <div className="space-y-3">
          {uploadableNeeded.map((item) => (
            <LockedPanel
              key={item.key}
              label={item.label}
              sector={item.sector}
              teaser={teaserFor(item.key, item.label)}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
