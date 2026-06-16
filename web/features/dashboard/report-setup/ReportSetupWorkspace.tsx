"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Card } from "@/components/ui/Card";
import { formatDate } from "@/lib/dashboard/utils";
import type {
  ReportSetupResponse,
  ReportSourceJob,
  SetupPreview,
  SetupWarning,
} from "@/lib/types/report";
import { SetupPreviewPanel } from "./SetupPreviewPanel";

function toggleId(ids: string[], id: string): string[] {
  return ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id];
}

export function ReportSetupWorkspace({ initial }: { initial: ReportSetupResponse }) {
  const router = useRouter();
  const [selected, setSelected] = useState<string[]>(initial.draft.source_job_ids);
  const [manualNotes, setManualNotes] = useState(initial.draft.manual_notes ?? "");
  const [excludedFindingIds, setExcludedFindingIds] = useState<string[]>(
    initial.draft.excluded_finding_ids ?? []
  );
  const [warnings, setWarnings] = useState<SetupWarning[]>(initial.warnings ?? []);
  const [preview, setPreview] = useState<SetupPreview | null>(initial.preview ?? null);
  const [pending, setPending] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const jobs = initial.available_jobs;

  const loadPreview = useCallback(async (jobIds: string[]) => {
    if (!jobIds.length) {
      setPreview(null);
      setWarnings([{ code: "empty", message: "Select at least one upload." }]);
      return;
    }
    const params = new URLSearchParams();
    for (const id of jobIds) params.append("job_ids", id);
    const res = await fetch(`/api/reports/setup/preview?${params}`);
    if (!res.ok) return;
    const data = (await res.json()) as ReportSetupResponse;
    setPreview(data.preview ?? null);
    setWarnings(data.warnings ?? []);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadPreview(selected);
    }, 300);
    return () => clearTimeout(timer);
  }, [selected, loadPreview]);

  const selectedJobs = useMemo(
    () => jobs.filter((j) => selected.includes(j.id)),
    [jobs, selected]
  );

  async function saveDraft() {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch("/api/reports/setup", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_job_ids: selected,
          manual_notes: manualNotes || null,
          excluded_finding_ids: excludedFindingIds,
        }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(data?.detail || "Failed to save setup");
      }
      const data = (await res.json()) as ReportSetupResponse;
      setWarnings(data.warnings ?? []);
      setPreview(data.preview ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save setup");
    } finally {
      setSaving(false);
    }
  }

  async function regenerate(mode: "full" | "ai_only" = "full") {
    setPending(true);
    setError(null);
    try {
      const res = await fetch("/api/reports/regenerate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_job_ids: selected,
          manual_notes: manualNotes || null,
          excluded_finding_ids: excludedFindingIds,
          mode,
        }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(data?.detail || "Regenerate failed");
      }
      const report = (await res.json()) as { id: string };
      router.push(`/dashboard/reports/${report.id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Regenerate failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-ribet-border bg-ribet-card/40 text-ribet-muted">
                <th className="px-4 py-3 font-medium">Include</th>
                <th className="px-4 py-3 font-medium">File</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Period</th>
                <th className="px-4 py-3 font-medium">Rows</th>
                <th className="px-4 py-3 font-medium">Uploaded</th>
              </tr>
            </thead>
            <tbody>
              {jobs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-ribet-muted">
                    No successful uploads yet. Upload ERP exports first.
                  </td>
                </tr>
              ) : (
                jobs.map((job: ReportSourceJob) => (
                  <tr key={job.id} className="border-b border-ribet-border/50 last:border-0">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selected.includes(job.id)}
                        onChange={() => setSelected((ids) => toggleId(ids, job.id))}
                        aria-label={`Include ${job.file_name}`}
                      />
                    </td>
                    <td className="px-4 py-3 text-ribet-text">{job.file_name}</td>
                    <td className="px-4 py-3 text-ribet-muted">
                      {job.report_type_label ?? job.report_type ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-ribet-muted">
                      {job.detected_period ?? "—"}
                    </td>
                    <td className="px-4 py-3 tabular-nums text-ribet-muted">
                      {job.row_count ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-ribet-muted">
                      {job.created_at ? formatDate(job.created_at) : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="space-y-3">
        <label htmlFor="manual-notes" className="text-sm font-semibold text-ribet-text">
          Business assumptions
        </label>
        <p className="text-xs text-ribet-muted">
          Ribet uses this as background context, not as numeric data. Manual context may
          explain business conditions but must not override evidence in the report.
        </p>
        <textarea
          id="manual-notes"
          rows={4}
          value={manualNotes}
          onChange={(e) => setManualNotes(e.target.value)}
          className="w-full rounded-xl border border-ribet-border bg-ribet-card px-3 py-2 text-sm text-ribet-text"
          placeholder="e.g. Q2 shutdown week explains lower production volumes…"
        />
      </Card>

      <SetupPreviewPanel preview={preview} warnings={warnings} />

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => void saveDraft()}
          disabled={saving || !selected.length}
          className="rounded-full border border-ribet-border px-5 py-2.5 text-sm font-medium text-ribet-text hover:bg-ribet-card disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save draft"}
        </button>
        <button
          type="button"
          onClick={() => void regenerate("full")}
          disabled={pending || !selected.length}
          className="rounded-full bg-ribet-green px-5 py-2.5 text-sm font-medium text-ribet-text hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Generating…" : "Regenerate report"}
        </button>
        <span className="text-xs text-ribet-muted">
          {selectedJobs.length} of {jobs.length} uploads selected
        </span>
      </div>

      {error && (
        <p className="text-sm text-ribet-risk" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
