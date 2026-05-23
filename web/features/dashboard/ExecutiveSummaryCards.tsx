import type { OperationalReport } from "@/lib/types/report";

export function ExecutiveSummaryCards({
  report,
}: {
  report: OperationalReport;
}) {
  const items = report.executive_summary.slice(0, 3);
  if (!items.length) return null;

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {items.map((line, i) => (
        <div
          key={i}
          className="rounded-2xl border border-rivet-border bg-rivet-card p-6"
        >
          <p className="text-sm text-rivet-muted">Signal {i + 1}</p>
          <p className="mt-2 text-lg font-semibold text-rivet-risk">{line}</p>
        </div>
      ))}
    </div>
  );
}
