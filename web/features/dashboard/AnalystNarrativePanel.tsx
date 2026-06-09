import { Card } from "@/components/ui/Card";
import type { AnalysisMetadata, AnalystOutput, ManagementQuestion } from "@/lib/types/report";

export function AnalystNarrativePanel({
  analystSummary,
  managementQuestions,
  metadata,
  executiveSummary,
  analystOutput,
}: {
  analystSummary?: string | null;
  managementQuestions?: string[];
  metadata?: AnalysisMetadata;
  executiveSummary: string[];
  analystOutput?: AnalystOutput | null;
}) {
  const narration = metadata?.narration ?? "legacy";
  const execBullets = analystOutput?.executive_summary?.length
    ? analystOutput.executive_summary
    : executiveSummary.slice(0, 5);
  const structuredQuestions: ManagementQuestion[] =
    analystOutput?.management_questions ?? [];
  const legacyQuestions = managementQuestions ?? [];
  const confidenceNotes = analystOutput?.confidence_notes ?? [];

  return (
    <Card className="space-y-6">
      {execBullets.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-ribet-text">Executive summary</h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ribet-text">
            {execBullets.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </section>
      )}

      <section className={execBullets.length > 0 ? "border-t border-ribet-border/60 pt-6" : ""}>
        <h3 className="text-sm font-semibold text-ribet-text">Analyst narrative</h3>
        {narration === "completed" && analystSummary ? (
          <p className="mt-3 text-sm leading-relaxed text-ribet-text">{analystSummary}</p>
        ) : narration === "fallback" ? (
          <p className="mt-3 text-sm text-ribet-muted">
            AI verification did not pass; showing deterministic analyst output built from
            your evidence pack.
          </p>
        ) : narration === "failed" ? (
          <p className="mt-3 text-sm text-ribet-muted">
            AI analysis could not be generated for this report. The items above are from
            deterministic analysis of your uploaded data.
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

      {confidenceNotes.length > 0 && (
        <section className="border-t border-ribet-border/60 pt-6">
          <h3 className="text-sm font-semibold text-ribet-text">Confidence & limitations</h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ribet-muted">
            {confidenceNotes.map((note, i) => (
              <li key={i}>{note}</li>
            ))}
          </ul>
        </section>
      )}

      {(structuredQuestions.length > 0 || legacyQuestions.length > 0) && (
        <section className="border-t border-ribet-border/60 pt-6">
          <h3 className="text-sm font-semibold text-ribet-text">Questions for management</h3>
          {structuredQuestions.length > 0 ? (
            <ul className="mt-3 space-y-4">
              {structuredQuestions.map((q, i) => (
                <li key={i} className="text-sm">
                  <p className="font-medium text-ribet-text">{q.question}</p>
                  {q.context && <p className="mt-1 text-ribet-muted">{q.context}</p>}
                </li>
              ))}
            </ul>
          ) : (
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ribet-text">
              {legacyQuestions.map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ul>
          )}
        </section>
      )}
    </Card>
  );
}
