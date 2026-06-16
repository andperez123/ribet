import { Card } from "@/components/ui/Card";
import { formatDate } from "@/lib/dashboard/utils";
import type { ReportSourceJob } from "@/lib/types/report";

export function ReportSourcesUsedPanel({ sources }: { sources: ReportSourceJob[] }) {
  if (!sources.length) return null;

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-ribet-text">Sources used</h2>
        <p className="mt-1 text-xs text-ribet-muted">
          Uploads included when this report was generated.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-ribet-border text-xs text-ribet-muted">
              <th className="pb-2 pr-4 font-medium">File</th>
              <th className="pb-2 pr-4 font-medium">Type</th>
              <th className="pb-2 pr-4 font-medium">Period</th>
              <th className="pb-2 pr-4 font-medium">Rows</th>
              <th className="pb-2 font-medium">Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.id} className="border-b border-ribet-border/50 last:border-0">
                <td className="py-2 pr-4 text-ribet-text">{s.file_name}</td>
                <td className="py-2 pr-4 text-ribet-muted">
                  {s.report_type_label ?? s.report_type ?? "—"}
                </td>
                <td className="py-2 pr-4 text-ribet-muted">{s.detected_period ?? "—"}</td>
                <td className="py-2 pr-4 tabular-nums text-ribet-muted">
                  {s.row_count ?? "—"}
                </td>
                <td className="py-2 text-ribet-muted">
                  {s.created_at ? formatDate(s.created_at) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
