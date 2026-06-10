"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

type QuestionOption = {
  value: string;
  label: string;
  description?: string;
  recommended?: boolean;
};

type IngestionQuestion = {
  id: string;
  question: string;
  reason: string;
  affected_fields?: string[];
  options?: QuestionOption[];
  required_before_analysis?: boolean;
};

type ColumnMapping = {
  source_column: string;
  canonical_field: string | null;
  confidence: number;
  reason: string;
  needs_user_confirmation: boolean;
};

type DataReview = {
  job_id: string;
  report_type?: string | null;
  mapping_confidence?: number | null;
  classification?: {
    likely_type?: string;
    label?: string;
    confidence?: number;
    evidence?: string[];
    alternative_types?: { type: string; label: string; confidence: number }[];
  };
  row_meaning?: {
    inferred?: string;
    inferred_label?: string;
    confidence?: number;
    effective?: string;
    effective_label?: string;
    options?: { value: string; label: string }[];
    user_confirmed?: string | null;
  };
  analysis_readiness?: {
    ready?: boolean;
    score?: number;
    blocking_reasons?: string[];
    required_questions?: string[];
  };
  column_mappings?: ColumnMapping[];
  missing_fields?: string[];
  questions?: IngestionQuestion[];
  schema_memory?: {
    match?: "auto_apply" | "suggest" | "none";
    prior_mapping?: Record<string, unknown>;
  };
  columns?: string[];
  sample_rows?: Record<string, string>[];
  mapping_answers?: Record<string, string>;
};

type Props = {
  jobId: string;
  fileName: string;
  onConfirmed?: (reportId: string) => void;
};

export function DataReviewPanel({ jobId, fileName, onConfirmed }: Props) {
  const [review, setReview] = useState<DataReview | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [assignments, setAssignments] = useState<Record<string, string>>({});
  const [applyMemory, setApplyMemory] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/ingest/jobs/${jobId}/mapping`);
        if (!res.ok) throw new Error("Could not load data review");
        const data = (await res.json()) as DataReview;
        if (!cancelled) {
          setReview(data);
          setAnswers(data.mapping_answers ?? {});
          const initial: Record<string, string> = {};
          for (const cm of data.column_mappings ?? []) {
            if (cm.canonical_field) {
              initial[cm.canonical_field] = cm.source_column;
            }
          }
          setAssignments(initial);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load data review");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  const columnOptions = useMemo(() => review?.columns ?? [], [review?.columns]);

  const columnMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const [canonical, source] of Object.entries(assignments)) {
      if (source) map[source] = canonical;
    }
    return map;
  }, [assignments]);

  const requiredUnanswered = useMemo(() => {
    return (review?.questions ?? []).filter(
      (q) => q.required_before_analysis && !answers[q.id]
    );
  }, [review?.questions, answers]);

  const confirm = useCallback(async () => {
    setConfirming(true);
    setError(null);
    try {
      const res = await fetch(`/api/ingest/jobs/${jobId}/mapping/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          column_map: columnMap,
          mapping_answers: answers,
          amount_strategy: answers.gl_amount_semantics,
          row_meaning: answers.row_meaning,
          apply_schema_memory: applyMemory ?? undefined,
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Confirm failed");
      }
      const job = (await res.json()) as { report_id?: string | null };
      if (job.report_id) onConfirmed?.(job.report_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Confirm failed");
    } finally {
      setConfirming(false);
    }
  }, [jobId, columnMap, answers, applyMemory, onConfirmed]);

  if (loading) {
    return (
      <Card className="flex items-center gap-2 text-sm text-ribet-muted">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading data review…
      </Card>
    );
  }

  if (!review) {
    return (
      <Card className="text-sm text-ribet-risk">
        {error ?? "Data review unavailable"}
      </Card>
    );
  }

  const classLabel = review.classification?.label ?? review.report_type ?? "Unknown";
  const classConf = Math.round((review.classification?.confidence ?? review.mapping_confidence ?? 0) * 100);
  const readinessScore = Math.round((review.analysis_readiness?.score ?? 0) * 100);
  const readinessReady = review.analysis_readiness?.ready;

  const detected = (review.column_mappings ?? []).filter((cm) => cm.canonical_field);
  const rowMeaningLabel =
    review.row_meaning?.effective_label ??
    review.row_meaning?.inferred_label ??
    "Not determined";

  return (
    <Card className="border-amber-500/30 bg-amber-500/5">
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-sm font-semibold text-ribet-text">Data Review — {fileName}</p>
        {review.report_type && <Badge variant="muted">{review.report_type}</Badge>}
      </div>

      <div className="mt-3 space-y-1 text-sm">
        <p className="text-ribet-text">
          Ribet thinks this file is <strong>{classLabel}</strong> with{" "}
          <strong>{classConf}%</strong> classification confidence.
        </p>
        <p className="text-ribet-muted">
          Analysis readiness: <strong>{readinessScore}%</strong>
          {readinessReady ? " — ready" : " — blocked until you confirm mappings below"}
        </p>
      </div>

      {(review.analysis_readiness?.blocking_reasons?.length ?? 0) > 0 && (
        <ul className="mt-2 text-xs text-amber-200/90">
          {review.analysis_readiness?.blocking_reasons?.map((r) => (
            <li key={r}>• {r}</li>
          ))}
        </ul>
      )}

      <section className="mt-4">
        <h3 className="text-sm font-semibold text-ribet-text">What one row means</h3>
        <p className="mt-1 text-xs text-ribet-muted">{rowMeaningLabel}</p>
        {(review.row_meaning?.options?.length ?? 0) > 0 && (
          <div className="mt-2 space-y-1">
            {(review.row_meaning?.options ?? []).map((opt) => (
              <label key={opt.value} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="row_meaning"
                  value={opt.value}
                  checked={answers.row_meaning === opt.value}
                  onChange={() => setAnswers((prev) => ({ ...prev, row_meaning: opt.value }))}
                />
                {opt.label}
              </label>
            ))}
          </div>
        )}
      </section>

      {review.schema_memory?.match === "suggest" && (
        <section className="mt-4 rounded-lg border border-ribet-border bg-ribet-bg/50 p-3">
          <p className="text-sm text-ribet-text">
            Ribet found a previous mapping for this schema. Apply it?
          </p>
          <div className="mt-2 flex gap-3">
            <button
              type="button"
              className="text-sm text-ribet-green hover:underline"
              onClick={() => setApplyMemory(true)}
            >
              Yes, apply
            </button>
            <button
              type="button"
              className="text-sm text-ribet-muted hover:underline"
              onClick={() => setApplyMemory(false)}
            >
              No, review manually
            </button>
          </div>
        </section>
      )}

      {detected.length > 0 && (
        <section className="mt-4">
          <h3 className="text-sm font-semibold text-ribet-text">Detected</h3>
          <ul className="mt-1 space-y-1 text-xs text-ribet-muted">
            {detected.map((cm) => (
              <li key={cm.source_column}>
                {cm.canonical_field?.replace(/_/g, " ")}: <code>{cm.source_column}</code>
                {cm.needs_user_confirmation && " (needs confirmation)"}
              </li>
            ))}
          </ul>
        </section>
      )}

      {(review.missing_fields?.length ?? 0) > 0 && (
        <section className="mt-4">
          <h3 className="text-sm font-semibold text-ribet-text">Missing</h3>
          <p className="mt-1 text-xs text-ribet-muted">
            {review.missing_fields?.join(", ")}
          </p>
        </section>
      )}

      {(review.questions?.length ?? 0) > 0 && (
        <section className="mt-4 space-y-4">
          <h3 className="text-sm font-semibold text-ribet-text">Needs confirmation</h3>
          {review.questions?.map((q) => (
            <div key={q.id} className="rounded-lg border border-ribet-border bg-ribet-bg/30 p-3">
              <p className="text-sm font-medium text-ribet-text">{q.question}</p>
              <p className="mt-1 text-xs text-ribet-muted">{q.reason}</p>
              {(q.options?.length ?? 0) > 0 ? (
                <div className="mt-2 space-y-1">
                  {q.options?.map((opt) => (
                    <label key={opt.value} className="flex items-start gap-2 text-sm">
                      <input
                        type="radio"
                        name={q.id}
                        value={opt.value}
                        checked={answers[q.id] === opt.value}
                        onChange={() => setAnswers((prev) => ({ ...prev, [q.id]: opt.value }))}
                        className="mt-1"
                      />
                      <span>
                        {opt.label}
                        {opt.recommended && (
                          <span className="ml-1 text-xs text-ribet-green">(recommended)</span>
                        )}
                        {opt.description && (
                          <span className="block text-xs text-ribet-muted">{opt.description}</span>
                        )}
                      </span>
                    </label>
                  ))}
                </div>
              ) : (
                <select
                  value={answers[q.id] ?? ""}
                  onChange={(e) =>
                    setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))
                  }
                  className="mt-2 w-full rounded-lg border border-ribet-border bg-ribet-bg px-3 py-2 text-sm"
                >
                  <option value="">— select column —</option>
                  {columnOptions.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              )}
            </div>
          ))}
        </section>
      )}

      {error && (
        <p className="mt-2 text-sm text-ribet-risk" role="alert">
          {error}
        </p>
      )}

      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={confirm}
          disabled={confirming || requiredUnanswered.length > 0}
          className="rounded-full bg-ribet-green px-4 py-2 text-sm font-medium text-ribet-text hover:opacity-90 disabled:opacity-50"
        >
          {confirming ? "Confirming…" : "Confirm and analyze"}
        </button>
        {requiredUnanswered.length > 0 && (
          <span className="self-center text-xs text-ribet-muted">
            Answer required questions to continue
          </span>
        )}
        <Link href="/dashboard" className="self-center text-sm text-ribet-muted hover:text-ribet-text">
          Dashboard
        </Link>
      </div>
    </Card>
  );
}
