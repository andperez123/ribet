import { Card } from "@/components/ui/Card";
import { formatDate } from "@/lib/dashboard/utils";
import type { EvidenceSummary } from "@/lib/types/report";

type Props = {
  evidencePack?: Record<string, unknown> | null;
  evidenceSummary?: EvidenceSummary | null;
  generatedAt?: string;
};

function readPackField(pack: Record<string, unknown>, key: string): unknown {
  return pack[key];
}

export function EvidencePackPanel({
  evidencePack,
  evidenceSummary,
  generatedAt,
}: Props) {
  if (!evidencePack && !evidenceSummary) return null;

  const schemaVersion =
    evidenceSummary?.schema_version ??
    (readPackField(evidencePack ?? {}, "schema_version") as string | undefined) ??
    "evidence_pack.v1";
  const packGenerated =
    evidenceSummary?.generated_at ??
    (readPackField(evidencePack ?? {}, "generated_at") as string | undefined);
  const metricCount =
    evidenceSummary?.metric_count ??
    Object.keys(
      (readPackField(evidencePack ?? {}, "metrics") as Record<string, unknown>) ?? {}
    ).length;
  const findingCount =
    evidenceSummary?.finding_count ??
    ((readPackField(evidencePack ?? {}, "findings") as unknown[]) ?? []).length;
  const domainCount =
    evidenceSummary?.coverage_domains ??
    Object.values(
      ((readPackField(evidencePack ?? {}, "coverage") as Record<string, unknown>)
        ?.domains as Record<string, boolean>) ?? {}
    ).filter(Boolean).length;
  const confidence =
    evidenceSummary?.confidence_score ??
    (
      readPackField(evidencePack ?? {}, "confidence") as {
        legacy_score?: number;
      }
    )?.legacy_score;

  return (
    <div id="evidence-pack-detail">
      <Card className="border-dashed border-ribet-border/80">
      <h2 className="text-sm font-semibold text-ribet-text">Evidence Pack detail</h2>
      <p className="mt-1 text-xs text-ribet-muted">Admin view — full evidence assembly metadata.</p>
      <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs text-ribet-muted">Version</dt>
          <dd className="font-mono text-ribet-text">{schemaVersion}</dd>
        </div>
        <div>
          <dt className="text-xs text-ribet-muted">Generated</dt>
          <dd className="text-ribet-text">
            {packGenerated ? formatDate(packGenerated) : generatedAt ? formatDate(generatedAt) : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-ribet-muted">Metrics</dt>
          <dd className="tabular-nums text-ribet-text">{metricCount}</dd>
        </div>
        <div>
          <dt className="text-xs text-ribet-muted">Findings</dt>
          <dd className="tabular-nums text-ribet-text">{findingCount}</dd>
        </div>
        <div>
          <dt className="text-xs text-ribet-muted">Coverage domains</dt>
          <dd className="tabular-nums text-ribet-text">{domainCount}</dd>
        </div>
        <div>
          <dt className="text-xs text-ribet-muted">Confidence</dt>
          <dd className="tabular-nums text-ribet-text">
            {confidence != null ? `${confidence}%` : "—"}
          </dd>
        </div>
      </dl>
      </Card>
    </div>
  );
}
