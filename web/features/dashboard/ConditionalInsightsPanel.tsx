import { Card } from "@/components/ui/Card";
import type { AnalystOutput } from "@/lib/types/report";

export function ConditionalInsightsPanel({
  analystOutput,
}: {
  analystOutput?: AnalystOutput | null;
}) {
  const items = analystOutput?.conditional_insights ?? [];
  if (!items.length) return null;

  return (
    <Card className="space-y-4">
      <h3 className="text-sm font-semibold text-ribet-text">Locked capabilities</h3>
      <ul className="space-y-3">
        {items.map((item, i) => (
          <li key={i} className="rounded-xl border border-dashed border-ribet-border/60 p-4">
            <p className="text-xs uppercase tracking-wide text-ribet-muted">
              {item.locked_capability.replace(/_/g, " ")}
            </p>
            <p className="mt-2 text-sm text-ribet-text">{item.insight}</p>
            <p className="mt-1 text-xs text-ribet-muted">
              Upload: {item.requires_upload}
            </p>
          </li>
        ))}
      </ul>
    </Card>
  );
}
