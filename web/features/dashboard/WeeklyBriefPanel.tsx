import { Card } from "@/components/ui/Card";
import { BRIEF_SECTION_LABELS } from "@/lib/dashboard/utils";
import type { WeeklyBrief } from "@/lib/types/report";

function isNeutralBriefLine(line: string): boolean {
  const lower = line.toLowerCase();
  return (
    lower.includes("within") ||
    lower.includes("below") ||
    lower.includes("no adjustment") ||
    lower.includes("tracked")
  );
}

export function WeeklyBriefPanel({ brief }: { brief: WeeklyBrief }) {
  const entries = Object.entries(brief.sections).filter(
    ([, items]) => items.length > 0
  );

  if (!entries.length) {
    return (
      <Card>
        <h3 className="text-sm font-semibold text-ribet-text">Weekly brief</h3>
        <p className="mt-3 text-sm text-ribet-muted">
          No domain data available for a weekly brief yet.
        </p>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="text-sm font-semibold text-ribet-text">Weekly brief</h3>
      <p className="mt-1 text-xs text-ribet-muted capitalize">{brief.period}</p>
      <div className="mt-6 space-y-6">
        {entries.map(([key, items]) => (
          <div key={key}>
            <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
              {BRIEF_SECTION_LABELS[key] ?? key.replace(/_/g, " ")}
            </p>
            <ul className="mt-2 space-y-1.5 text-sm">
              {items.map((item, i) => (
                <li
                  key={i}
                  className={
                    isNeutralBriefLine(item)
                      ? "text-ribet-muted"
                      : "text-ribet-text"
                  }
                >
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
