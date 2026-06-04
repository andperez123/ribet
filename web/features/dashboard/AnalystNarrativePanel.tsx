import { Card } from "@/components/ui/Card";
import type { AnalysisMetadata } from "@/lib/types/report";

export function AnalystNarrativePanel({
  analystSummary,
  managementQuestions,
  metadata,
  executiveSummary,
}: {
  analystSummary?: string | null;
  managementQuestions?: string[];
  metadata?: AnalysisMetadata;
  executiveSummary: string[];
}) {
  const narration = metadata?.narration ?? "legacy";
  const questions = managementQuestions ?? [];

  return (
    <Card>
      <h3 className="text-sm font-semibold text-ribet-text">Analysis</h3>
      {narration === "completed" && analystSummary ? (
        <p className="mt-3 text-sm leading-relaxed text-ribet-text">
          {analystSummary}
        </p>
      ) : narration === "failed" ? (
        <p className="mt-3 text-sm text-ribet-muted">
          AI analysis could not be generated for this report. Review the
          deterministic insights below.
        </p>
      ) : narration === "skipped" ? (
        <p className="mt-3 text-sm text-ribet-muted">
          Deterministic analysis only — AI narration is not enabled for this
          environment.
        </p>
      ) : (
        <p className="mt-3 text-sm text-ribet-muted">
          Deterministic analysis from uploaded data
          {metadata?.data_domains_present?.length
            ? ` (${metadata.data_domains_present.join(", ")})`
            : ""}
          .
        </p>
      )}

      {executiveSummary.length > 0 && (
        <div className="mt-4 border-t border-ribet-border/60 pt-4">
          <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Executive summary
          </p>
          <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-ribet-muted">
            {executiveSummary.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </div>
      )}

      {questions.length > 0 && (
        <div className="mt-4 border-t border-ribet-border/60 pt-4">
          <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
            Questions for management
          </p>
          <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-ribet-text">
            {questions.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
