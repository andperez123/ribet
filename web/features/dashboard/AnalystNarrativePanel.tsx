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
  const whatMatters = executiveSummary.slice(0, 5);

  return (
    <Card className="space-y-6">
      {whatMatters.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-ribet-text">What matters</h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ribet-text">
            {whatMatters.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </section>
      )}

      <section className={whatMatters.length > 0 ? "border-t border-ribet-border/60 pt-6" : ""}>
        <h3 className="text-sm font-semibold text-ribet-text">Analyst narrative</h3>
        {narration === "completed" && analystSummary ? (
          <p className="mt-3 text-sm leading-relaxed text-ribet-text">
            {analystSummary}
          </p>
        ) : narration === "failed" ? (
          <p className="mt-3 text-sm text-ribet-muted">
            AI analysis could not be generated for this report. The items above
            are from deterministic analysis of your uploaded data.
          </p>
        ) : (
          <p className="mt-3 text-sm text-ribet-muted">
            Deterministic analysis from uploaded data
            {metadata?.data_domains_present?.length
              ? ` (${metadata.data_domains_present.join(", ")})`
              : ""}
            . Enable AI narration for a controller-facing narrative summary.
          </p>
        )}
      </section>

      {questions.length > 0 && (
        <section className="border-t border-ribet-border/60 pt-6">
          <h3 className="text-sm font-semibold text-ribet-text">
            Questions for management
          </h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ribet-text">
            {questions.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </section>
      )}
    </Card>
  );
}
