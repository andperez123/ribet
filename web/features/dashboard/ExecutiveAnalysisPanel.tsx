"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import type { AnalysisMetadata, AnalystOutput, ManagementQuestion } from "@/lib/types/report";

export function ExecutiveAnalysisPanel({
  analystSummary,
  managementQuestions,
  metadata,
  executiveSummary,
  analystOutput,
  verifiedFindings,
}: {
  analystSummary?: string | null;
  managementQuestions?: string[];
  metadata?: AnalysisMetadata;
  executiveSummary: string[];
  analystOutput?: AnalystOutput | null;
  verifiedFindings?: string[];
}) {
  const [showAi, setShowAi] = useState(false);
  const narration = metadata?.narration ?? "legacy";
  const verifiedBullets =
    verifiedFindings ??
    (analystOutput?.executive_summary?.length
      ? analystOutput.executive_summary
      : executiveSummary.slice(0, 5));
  const structuredQuestions: ManagementQuestion[] =
    analystOutput?.management_questions ?? [];
  const legacyQuestions = managementQuestions ?? [];
  const confidenceNotes = analystOutput?.confidence_notes ?? [];
  const verificationPassed =
    (metadata as { verification_status?: string })?.verification_status === "passed";

  return (
    <Card className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-ribet-text">Executive analysis</h2>
        <p className="mt-1 text-sm text-ribet-muted">
          Verified findings and optional AI interpretation.
        </p>
      </div>

      {verifiedBullets.length > 0 && (
        <section>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-ribet-text">Verified findings</h3>
            <span className="rounded-full border border-ribet-green/40 bg-ribet-green/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-ribet-green">
              Verified · Evidence Pack
            </span>
          </div>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-ribet-text">
            {verifiedBullets.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </section>
      )}

      {(narration === "completed" && analystSummary) ||
      narration === "fallback" ||
      narration === "failed" ||
      narration === "skipped" ? (
        <section className="border-t border-ribet-border/60 pt-6">
          <button
            type="button"
            onClick={() => setShowAi((v) => !v)}
            className="flex w-full items-center justify-between text-left"
          >
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-semibold text-ribet-text">AI interpretation</h3>
              {verificationPassed && (
                <span className="text-[10px] uppercase tracking-wide text-ribet-muted">
                  Verified
                </span>
              )}
            </div>
            <span className="text-xs text-ribet-muted">{showAi ? "Hide" : "Show"}</span>
          </button>
          {showAi && (
            <div className="mt-3">
              {narration === "completed" && analystSummary ? (
                <p className="text-sm leading-relaxed text-ribet-text">{analystSummary}</p>
              ) : narration === "fallback" ? (
                <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-ribet-text">
                  Showing verified findings only — AI verification did not pass for this
                  report.
                </p>
              ) : (
                <p className="text-sm text-ribet-muted">
                  AI interpretation was not generated. Verified findings above are from
                  deterministic analysis of your uploaded data.
                </p>
              )}
            </div>
          )}
        </section>
      ) : null}

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
          <h3 className="text-sm font-semibold text-ribet-text">Management questions</h3>
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
            <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-ribet-text">
              {legacyQuestions.map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ol>
          )}
        </section>
      )}
    </Card>
  );
}
