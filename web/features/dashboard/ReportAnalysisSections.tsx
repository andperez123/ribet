import { DataDigestKpiGrid } from "@/features/dashboard/DataDigestKpiGrid";
import { InsightCardsGrid } from "@/features/dashboard/InsightCardsGrid";
import { Card } from "@/components/ui/Card";
import type { DataCoverage, DataDigest, DomainInsight } from "@/lib/types/report";

export function OrgWideSynthesisPanel({
  synthesis,
}: {
  synthesis?: {
    org_context_domains?: string[];
    digest?: DataDigest;
    synthesis_insights?: DomainInsight[];
  } | null;
}) {
  if (!synthesis?.digest) return null;

  const domains = synthesis.org_context_domains ?? [];
  const digest = synthesis.digest;
  const coverage: DataCoverage = {
    ar: domains.includes("ar"),
    ap: domains.includes("ap"),
    gl: domains.includes("gl"),
    inventory: domains.includes("inventory"),
    primary_domain: null,
  };

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ribet-text">
          Your operational picture
        </h2>
        <p className="mt-1 text-sm text-ribet-muted">
          Cross-domain synthesis from all data Ribet currently understands
          {domains.length ? ` (${domains.join(", ")})` : ""}.
        </p>
      </div>
      <DataDigestKpiGrid digest={digest} coverage={coverage} />
      {synthesis.synthesis_insights && synthesis.synthesis_insights.length > 0 ? (
        <InsightCardsGrid insights={synthesis.synthesis_insights} />
      ) : (
        <Card className="border-dashed">
          <p className="text-sm text-ribet-muted">
            Upload additional report types to unlock cross-domain insights.
          </p>
        </Card>
      )}
    </section>
  );
}

export function PrimaryAnalysisPanel({
  primary,
  digest,
  coverage,
  insights,
}: {
  primary?: {
    triggered_by?: string[];
    source_traceability?: { upload_label?: string; period?: string; row_count?: number };
  };
  digest: DataDigest;
  coverage: DataCoverage;
  insights: DomainInsight[];
}) {
  const trace = primary?.source_traceability;

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ribet-text">
          What this upload tells us
        </h2>
        {trace?.upload_label && (
          <p className="mt-1 text-sm text-ribet-muted">
            Based on: {trace.upload_label}
            {trace.period ? ` · ${trace.period}` : ""}
            {trace.row_count != null ? ` · ${trace.row_count} rows analyzed` : ""}
          </p>
        )}
      </div>
      <DataDigestKpiGrid digest={digest} coverage={coverage} />
      <InsightCardsGrid insights={insights} />
    </section>
  );
}
