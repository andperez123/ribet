import Link from "next/link";
import { Card } from "@/components/ui/Card";
import type {
  AnalysisMetadata,
  DataCoverage,
  DataDigest,
  EvidenceSummary,
} from "@/lib/types/report";

type Props = {
  digest: DataDigest;
  coverage: DataCoverage;
  metadata: AnalysisMetadata;
  rulesExecuted?: number;
  evidenceSummary?: EvidenceSummary | null;
  hasEvidencePack?: boolean;
  showAdminLink?: boolean;
};

function formatCount(n: number, unit: string): string {
  return `${n.toLocaleString()} ${unit}`;
}

export function EvidenceSummaryPanel({
  digest,
  coverage,
  metadata,
  rulesExecuted,
  evidenceSummary,
  hasEvidencePack,
  showAdminLink,
}: Props) {
  const sources: Array<{ label: string; detail: string }> = [];

  if (coverage.ar && digest.ar_invoice_count > 0) {
    sources.push({
      label: "AR Aging",
      detail: formatCount(digest.ar_invoice_count, "invoices analyzed"),
    });
  }
  if (coverage.ap && digest.vendor_count > 0) {
    sources.push({
      label: "AP Aging",
      detail: formatCount(digest.vendor_count, "vendor balances analyzed"),
    });
  }
  if (coverage.gl && digest.gl_txn_count > 0) {
    sources.push({
      label: "GL Detail",
      detail: formatCount(digest.gl_txn_count, "transactions analyzed"),
    });
  }
  if (coverage.inventory && digest.inventory_item_count > 0) {
    sources.push({
      label: "Inventory",
      detail: formatCount(digest.inventory_item_count, "SKUs analyzed"),
    });
  }

  if (evidenceSummary?.sources?.length) {
    sources.length = 0;
    for (const s of evidenceSummary.sources) {
      sources.push({ label: s.label, detail: s.detail });
    }
  }

  const rulesCount = evidenceSummary?.rules_executed ?? rulesExecuted ?? metadata.finding_count;
  const verified = hasEvidencePack || Boolean(evidenceSummary);

  if (!sources.length && !rulesCount) return null;

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-ribet-text">Evidence summary</h2>
          <p className="mt-1 text-sm text-ribet-muted">
            Deterministic analysis from uploaded ERP exports.
          </p>
        </div>
        {verified && (
          <span className="rounded-full border border-ribet-green/40 bg-ribet-green/10 px-3 py-1 text-xs font-medium text-ribet-green">
            Verified by Evidence Pack
          </span>
        )}
      </div>

      {sources.length > 0 && (
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Evidence sources
          </p>
          <ul className="mt-2 space-y-2">
            {sources.map((s) => (
              <li key={s.label} className="flex flex-wrap justify-between gap-2 text-sm">
                <span className="font-medium text-ribet-text">{s.label}</span>
                <span className="text-ribet-muted">{s.detail}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {rulesCount > 0 && (
        <p className="text-sm text-ribet-text">
          <span className="font-medium">Rules executed</span>{" "}
          <span className="tabular-nums text-ribet-muted">— {rulesCount}</span>
        </p>
      )}

      {showAdminLink && hasEvidencePack && (
        <Link
          href="#evidence-pack-detail"
          className="text-sm font-medium text-ribet-green hover:underline"
        >
          View full evidence →
        </Link>
      )}
    </Card>
  );
}
