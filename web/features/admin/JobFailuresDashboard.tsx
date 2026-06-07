"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import type { AdminJobFailure, AdminJobFailuresResponse } from "@/lib/types/admin";

function formatWhen(iso: string) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

function codeVariant(code: string | null) {
  if (!code) return "muted" as const;
  if (code.includes("excel") || code === "legacy_excel") return "risk" as const;
  if (code === "unknown_report_type") return "default" as const;
  return "muted" as const;
}

function FailureRow({ failure }: { failure: AdminJobFailure }) {
  const hint = failure.job_errors[0]?.hint;

  return (
    <details className="group rounded-xl border border-ribet-border bg-ribet-card">
      <summary className="cursor-pointer list-none px-4 py-3 [&::-webkit-details-marker]:hidden">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <p className="truncate font-medium text-ribet-text">
                {failure.file_name ?? "(unknown file)"}
              </p>
              {failure.error_code && (
                <Badge variant={codeVariant(failure.error_code)}>
                  {failure.error_code}
                </Badge>
              )}
            </div>
            <p className="mt-1 text-sm text-ribet-muted">
              {failure.error_message ?? "Processing failed"}
            </p>
            <p className="mt-1 text-xs text-ribet-muted">
              {failure.org_name ?? "Unknown org"}
              {failure.sector ? ` · ${failure.sector}` : ""}
              {" · "}
              {formatWhen(failure.created_at)}
            </p>
          </div>
          <span className="text-xs text-ribet-muted group-open:hidden">Expand</span>
        </div>
      </summary>

      <div className="space-y-3 border-t border-ribet-border px-4 py-3 text-sm">
        {hint && (
          <p className="text-ribet-muted">
            <span className="font-medium text-ribet-text">User hint: </span>
            {hint}
          </p>
        )}

        <dl className="grid gap-2 font-mono text-xs md:grid-cols-2">
          <div>
            <dt className="text-ribet-muted">Job ID</dt>
            <dd className="break-all text-ribet-text">{failure.job_id ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-ribet-muted">Event ID</dt>
            <dd className="break-all text-ribet-text">{failure.event_id}</dd>
          </div>
          <div>
            <dt className="text-ribet-muted">Org ID</dt>
            <dd className="break-all text-ribet-text">{failure.org_id ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-ribet-muted">Job status</dt>
            <dd className="text-ribet-text">{failure.job_status ?? "—"}</dd>
          </div>
        </dl>

        {failure.error_detail && (
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
              Error detail
            </p>
            <pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-ribet-bg/80 p-3 font-mono text-[11px] text-ribet-text">
              {failure.error_detail}
            </pre>
          </div>
        )}

        {failure.intake_metadata && (
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
              Intake metadata
            </p>
            <pre className="mt-1 overflow-auto rounded-lg bg-ribet-bg/80 p-3 font-mono text-[11px] text-ribet-text">
              {JSON.stringify(failure.intake_metadata, null, 2)}
            </pre>
          </div>
        )}

        {failure.job_errors.length > 1 && (
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
              All stored errors
            </p>
            <pre className="mt-1 overflow-auto rounded-lg bg-ribet-bg/80 p-3 font-mono text-[11px] text-ribet-text">
              {JSON.stringify(failure.job_errors, null, 2)}
            </pre>
          </div>
        )}

        <p className="text-[11px] text-ribet-muted">
          Grep worker logs:{" "}
          <code className="text-ribet-text">
            job_failed job_id={failure.job_id ?? "…"}
          </code>
        </p>
      </div>
    </details>
  );
}

export function JobFailuresDashboard({
  data,
}: {
  data: AdminJobFailuresResponse;
}) {
  const [query, setQuery] = useState("");
  const [codeFilter, setCodeFilter] = useState<string>("all");

  const codes = useMemo(() => {
    const set = new Set<string>();
    for (const f of data.failures) {
      if (f.error_code) set.add(f.error_code);
    }
    return [...set].sort();
  }, [data.failures]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return data.failures.filter((f) => {
      if (codeFilter !== "all" && f.error_code !== codeFilter) return false;
      if (!q) return true;
      const haystack = [
        f.file_name,
        f.org_name,
        f.error_message,
        f.error_detail,
        f.error_code,
        f.job_id,
        f.org_id,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [data.failures, query, codeFilter]);

  const byCode = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const f of data.failures) {
      const key = f.error_code ?? "unknown";
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [data.failures]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ribet-text">
          Job failures
        </h1>
        <p className="mt-1 text-sm text-ribet-muted">
          Recent ingest failures from <code>job_failed</code> events — use this
          to debug CSV vs Excel issues and report-type mismatches.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="text-sm text-ribet-muted">Recent failures</p>
          <p className="mt-2 text-3xl font-semibold text-ribet-text">
            {data.total}
          </p>
        </Card>
        {byCode.slice(0, 3).map(([code, count]) => (
          <Card key={code}>
            <p className="truncate text-sm text-ribet-muted">{code}</p>
            <p className="mt-2 text-3xl font-semibold text-ribet-text">{count}</p>
          </Card>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search file, org, job ID, error…"
          className="min-w-[220px] flex-1 rounded-lg border border-ribet-border bg-ribet-card px-3 py-2 text-sm text-ribet-text"
        />
        <select
          value={codeFilter}
          onChange={(e) => setCodeFilter(e.target.value)}
          className="rounded-lg border border-ribet-border bg-ribet-card px-3 py-2 text-sm text-ribet-text"
        >
          <option value="all">All error codes</option>
          {codes.map((code) => (
            <option key={code} value={code}>
              {code}
            </option>
          ))}
        </select>
      </div>

      {filtered.length === 0 ? (
        <Card className="text-center">
          <p className="text-sm text-ribet-muted">
            {data.failures.length === 0
              ? "No job failures recorded yet."
              : "No failures match your filters."}
          </p>
        </Card>
      ) : (
        <div className="space-y-2">
          {filtered.map((failure) => (
            <FailureRow key={failure.event_id} failure={failure} />
          ))}
        </div>
      )}
    </div>
  );
}
