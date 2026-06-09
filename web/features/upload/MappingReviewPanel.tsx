"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

type MappingReview = {
  job_id: string;
  report_type?: string | null;
  mapping_confidence?: number | null;
  columns?: string[];
  canonical_fields?: string[];
  unmapped_columns?: string[];
  mapping?: {
    field_mapping?: Record<string, { source?: string; confidence?: number }>;
    unmapped_columns?: string[];
    parse_warnings?: string[];
  };
};

type Props = {
  jobId: string;
  fileName: string;
  onConfirmed?: (reportId: string) => void;
};

export function MappingReviewPanel({ jobId, fileName, onConfirmed }: Props) {
  const [review, setReview] = useState<MappingReview | null>(null);
  const [assignments, setAssignments] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`/api/ingest/jobs/${jobId}/mapping`);
        if (!res.ok) throw new Error("Could not load mapping review");
        const data = (await res.json()) as MappingReview;
        if (!cancelled) {
          setReview(data);
          const initial: Record<string, string> = {};
          for (const [field, meta] of Object.entries(data.mapping?.field_mapping ?? {})) {
            if (meta.source) initial[field] = meta.source;
          }
          setAssignments(initial);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load mapping");
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
  const canonicalFields = useMemo(
    () => review?.canonical_fields ?? Object.keys(review?.mapping?.field_mapping ?? {}),
    [review]
  );

  const columnMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const [canonical, source] of Object.entries(assignments)) {
      if (source) map[source] = canonical;
    }
    return map;
  }, [assignments]);

  const confirm = useCallback(async () => {
    setConfirming(true);
    setError(null);
    try {
      const res = await fetch(`/api/ingest/jobs/${jobId}/mapping/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ column_map: columnMap }),
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
  }, [jobId, columnMap, onConfirmed]);

  if (loading) {
    return (
      <Card className="flex items-center gap-2 text-sm text-ribet-muted">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading column mapping…
      </Card>
    );
  }

  if (!review) {
    return (
      <Card className="text-sm text-ribet-risk">
        {error ?? "Mapping review unavailable"}
      </Card>
    );
  }

  return (
    <Card className="border-amber-500/30 bg-amber-500/5">
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-sm font-semibold text-ribet-text">
          Review column mapping — {fileName}
        </p>
        {review.report_type && <Badge variant="muted">{review.report_type}</Badge>}
        {review.mapping_confidence != null && (
          <Badge variant="muted">
            {Math.round(review.mapping_confidence * 100)}% confidence
          </Badge>
        )}
      </div>
      <p className="mt-2 text-sm text-ribet-muted">
        Adjust how your file columns map to Ribet fields, then confirm to run analysis.
        Corrections are remembered for future uploads with the same layout.
      </p>

      {canonicalFields.length > 0 && (
        <div className="mt-4 space-y-3">
          {canonicalFields.map((field) => (
            <label key={field} className="block text-sm">
              <span className="font-medium text-ribet-text">{field.replace(/_/g, " ")}</span>
              <select
                value={assignments[field] ?? ""}
                onChange={(e) =>
                  setAssignments((prev) => ({ ...prev, [field]: e.target.value }))
                }
                className="mt-1 w-full rounded-lg border border-ribet-border bg-ribet-bg px-3 py-2 text-sm text-ribet-text"
              >
                <option value="">— not mapped —</option>
                {columnOptions.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
      )}

      {(review.unmapped_columns?.length ?? 0) > 0 && (
        <p className="mt-3 text-xs text-ribet-muted">
          Extra columns preserved for context: {review.unmapped_columns?.join(", ")}
        </p>
      )}

      {(review.mapping?.parse_warnings?.length ?? 0) > 0 && (
        <ul className="mt-2 text-xs text-amber-200/90">
          {review.mapping?.parse_warnings?.map((w) => (
            <li key={w}>• {w}</li>
          ))}
        </ul>
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
          disabled={confirming}
          className="rounded-full bg-ribet-green px-4 py-2 text-sm font-medium text-ribet-text hover:opacity-90 disabled:opacity-50"
        >
          {confirming ? "Confirming…" : "Confirm and analyze"}
        </button>
        <Link
          href="/dashboard"
          className="text-sm text-ribet-muted hover:text-ribet-text"
        >
          Dashboard
        </Link>
      </div>
    </Card>
  );
}
