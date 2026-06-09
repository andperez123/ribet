import { Card } from "@/components/ui/Card";
import type { AnalystOutput, BlockedAnalysis, ReportContract } from "@/lib/types/report";

type Props = {
  blockedAnalyses?: BlockedAnalysis[];
  coverageGaps?: ReportContract["coverage_gaps"];
  analystOutput?: AnalystOutput | null;
};

function fromContract(blocked: BlockedAnalysis[]) {
  return blocked.map((b) => ({
    name: b.analysis_name,
    requires: b.requires_uploads.join(", "),
  }));
}

function fromGapsAndInsights(
  coverageGaps?: ReportContract["coverage_gaps"],
  analystOutput?: AnalystOutput | null
) {
  const items: Array<{ name: string; requires: string }> = [];
  const seen = new Set<string>();

  const gapLabels: Record<string, { name: string; requires: string }> = {
    missing_sales_orders: {
      name: "Inventory vs Demand",
      requires: "Open Sales Orders",
    },
    missing_work_orders: {
      name: "Production Bottleneck Detection",
      requires: "Work Orders",
    },
    missing_gl_detail: {
      name: "Margin Leakage Analysis",
      requires: "GL Detail",
    },
    missing_purchase_orders: {
      name: "Vendor Fulfillment Analysis",
      requires: "Purchase Orders",
    },
    cash_pressure_diagnosis: {
      name: "Cash Pressure Diagnosis",
      requires: "AP Aging, Open Sales Orders, Purchase Orders",
    },
  };

  for (const gap of coverageGaps ?? []) {
    const mapped = gapLabels[gap.gap_type];
    if (mapped && !seen.has(mapped.name)) {
      seen.add(mapped.name);
      items.push({
        name: mapped.name,
        requires: gap.recommended_uploads?.join(", ") || mapped.requires,
      });
    }
  }

  if (!seen.has("Margin Leakage Analysis")) {
    const needsGl = coverageGaps?.some((g) =>
      g.recommended_uploads?.some((u) => u.toLowerCase().includes("gl"))
    );
    if (needsGl) {
      items.push({ name: "Margin Leakage Analysis", requires: "GL Detail" });
    }
  }

  for (const ci of analystOutput?.conditional_insights ?? []) {
    const name = ci.locked_capability.replace(/_/g, " ");
    const key = `${name}-${ci.requires_upload}`;
    if (seen.has(key)) continue;
    seen.add(key);
    items.push({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      requires: ci.requires_upload,
    });
  }

  return items;
}

export function BlockedAnalysesPanel({
  blockedAnalyses,
  coverageGaps,
  analystOutput,
}: Props) {
  const items = blockedAnalyses?.length
    ? fromContract(blockedAnalyses)
    : fromGapsAndInsights(coverageGaps, analystOutput);

  if (!items.length) return null;

  return (
    <Card className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold text-ribet-text">Blocked analyses</h2>
        <p className="mt-1 text-sm text-ribet-muted">
          These analyses cannot run until additional data is uploaded.
        </p>
      </div>
      <ul className="space-y-3">
        {items.map((item) => (
          <li
            key={`${item.name}-${item.requires}`}
            className="flex flex-wrap items-start gap-2 rounded-xl border border-dashed border-amber-500/40 bg-amber-500/5 px-4 py-3 text-sm"
          >
            <span className="text-ribet-risk" aria-hidden>
              ✕
            </span>
            <div>
              <p className="font-medium text-ribet-text">{item.name}</p>
              <p className="mt-0.5 text-ribet-muted">Requires {item.requires}</p>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
