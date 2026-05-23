import { Card } from "@/components/ui/Card";
import { BRIEF_SECTION_LABELS } from "@/lib/dashboard/utils";
import type { WeeklyBrief } from "@/lib/types/report";

export function WeeklyBriefPanel({ brief }: { brief: WeeklyBrief }) {
  const entries = Object.entries(brief.sections);

  return (
    <Card>
      <h3 className="text-sm font-semibold text-rivet-text">Weekly brief</h3>
      <p className="mt-1 text-xs text-rivet-muted capitalize">{brief.period}</p>
      <div className="mt-6 space-y-6">
        {entries.map(([key, items]) => (
          <div key={key}>
            <p className="text-xs font-medium uppercase tracking-wide text-rivet-muted">
              {BRIEF_SECTION_LABELS[key] ?? key.replace(/_/g, " ")}
            </p>
            <ul className="mt-2 space-y-1 text-sm text-rivet-text">
              {items.map((item, i) => (
                <li key={i} className="text-rivet-muted">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Card>
  );
}
