import { Card } from "@/components/ui/Card";
import { formatCurrency } from "@/lib/dashboard/utils";
import type { AnalysisMetadata, DataCoverage, DataDigest } from "@/lib/types/report";

export function ReportAnalysisDebugPanel({
  digest,
  coverage,
  metadata,
  orgId,
}: {
  digest: DataDigest;
  coverage: DataCoverage;
  metadata: AnalysisMetadata;
  orgId: string;
}) {
  const source = metadata.insights_source ?? metadata.narration;

  return (
    <Card className="border-dashed border-ribet-border/80 bg-ribet-card/40">
      <details>
        <summary className="cursor-pointer text-sm font-semibold text-ribet-text">
          Analysis details
        </summary>
        <div className="mt-4 grid gap-4 text-sm md:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
              Report metadata
            </p>
            <ul className="mt-2 space-y-1 text-ribet-muted">
              <li>
                <span className="text-ribet-text">Org:</span> {orgId}
              </li>
              <li>
                <span className="text-ribet-text">Insights source:</span> {source}
              </li>
              <li>
                <span className="text-ribet-text">Narration:</span> {metadata.narration}
              </li>
              <li>
                <span className="text-ribet-text">Findings:</span> {metadata.finding_count}
              </li>
              {metadata.duration_ms != null && (
                <li>
                  <span className="text-ribet-text">Narration duration:</span>{" "}
                  {metadata.duration_ms}ms
                </li>
              )}
            </ul>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
              Data digest
            </p>
            <ul className="mt-2 space-y-1 text-ribet-muted">
              <li>
                AR total:{" "}
                <span className="text-ribet-text">{formatCurrency(digest.ar_total)}</span>{" "}
                ({digest.ar_invoice_count} rows)
              </li>
              <li>
                AP total:{" "}
                <span className="text-ribet-text">{formatCurrency(digest.ap_total)}</span>{" "}
                ({digest.vendor_count} vendors)
              </li>
              <li>
                GL txns: <span className="text-ribet-text">{digest.gl_txn_count}</span>
              </li>
              <li>
                Inventory items:{" "}
                <span className="text-ribet-text">{digest.inventory_item_count}</span>
              </li>
              <li>
                Top customers:{" "}
                <span className="text-ribet-text">{digest.top_customers.length}</span>
              </li>
            </ul>
          </div>
          <div className="md:col-span-2">
            <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
              Coverage
            </p>
            <p className="mt-2 text-ribet-muted">
              AR {coverage.ar ? "yes" : "no"} · AP {coverage.ap ? "yes" : "no"} · GL{" "}
              {coverage.gl ? "yes" : "no"} · Inventory {coverage.inventory ? "yes" : "no"}
            </p>
            {metadata.data_domains_present?.length > 0 && (
              <p className="mt-1 text-xs text-ribet-muted">
                Domains at generation: {metadata.data_domains_present.join(", ")}
              </p>
            )}
            {source === "refreshed" && (
              <p className="mt-2 text-xs text-amber-600">
                Digest was recomputed from current database tables because the frozen
                report snapshot had no monetary data.
              </p>
            )}
            {source === "frozen" && digest.ar_invoice_count > 0 && digest.ar_total === 0 && (
              <p className="mt-2 text-xs text-amber-600">
                Frozen snapshot shows rows but $0 amounts. Re-upload after mapping fixes or
                check canonical tables.
              </p>
            )}
          </div>
        </div>
      </details>
    </Card>
  );
}
