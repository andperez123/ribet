"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Card } from "@/components/ui/Card";

type FindingRow = {
  finding_id?: string;
  title?: string;
};

export function EvidencePackEditor({
  evidencePack,
}: {
  evidencePack?: Record<string, unknown> | null;
}) {
  const router = useRouter();
  const findings = (evidencePack?.findings as FindingRow[] | undefined) ?? [];
  const [excluded, setExcluded] = useState<Set<string>>(new Set());
  const [boundaryNote, setBoundaryNote] = useState("");
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!findings.length) return null;

  async function saveToDraft() {
    setPending(true);
    setError(null);
    try {
      const res = await fetch("/api/reports/setup", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          excluded_finding_ids: Array.from(excluded),
          evidence_overrides: boundaryNote.trim()
            ? {
                analysis_boundaries: {
                  cannot_conclude: [boundaryNote.trim()],
                },
              }
            : {},
        }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(data?.detail || "Failed to save evidence adjustments");
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setPending(false);
    }
  }

  return (
    <Card className="border-dashed border-ribet-border/80">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="text-sm font-semibold text-ribet-text"
      >
        {open ? "Hide evidence adjustments" : "Adjust evidence inputs (admin)"}
      </button>
      {open && (
        <div className="mt-4 space-y-4 text-sm">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
              Exclude findings from evidence pack
            </p>
            <ul className="mt-2 space-y-2">
              {findings.map((f) => {
                const id = f.finding_id ?? f.title ?? "";
                if (!id) return null;
                return (
                  <li key={id} className="flex items-start gap-2">
                    <input
                      type="checkbox"
                      checked={excluded.has(id)}
                      onChange={() => {
                        setExcluded((prev) => {
                          const next = new Set(prev);
                          if (next.has(id)) next.delete(id);
                          else next.add(id);
                          return next;
                        });
                      }}
                    />
                    <span className="text-ribet-text">{f.title ?? id}</span>
                  </li>
                );
              })}
            </ul>
          </div>
          <div>
            <label className="text-xs font-medium text-ribet-muted">
              Additional cannot-conclude note
            </label>
            <textarea
              rows={2}
              value={boundaryNote}
              onChange={(e) => setBoundaryNote(e.target.value)}
              className="mt-1 w-full rounded-xl border border-ribet-border bg-ribet-card px-3 py-2 text-sm"
              placeholder="e.g. Margin analysis not possible without GL detail…"
            />
          </div>
          <button
            type="button"
            onClick={() => void saveToDraft()}
            disabled={pending}
            className="rounded-full border border-ribet-border px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {pending ? "Saving…" : "Save to setup draft"}
          </button>
          {error && (
            <p className="text-sm text-ribet-risk" role="alert">
              {error}
            </p>
          )}
        </div>
      )}
    </Card>
  );
}
