"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Card } from "@/components/ui/Card";

export function ReportNarrativeEditor({
  reportId,
  executiveSummary,
  managementQuestions,
}: {
  reportId: string;
  executiveSummary: string[];
  managementQuestions: string[];
}) {
  const router = useRouter();
  const [summaryText, setSummaryText] = useState(executiveSummary.join("\n"));
  const [questionsText, setQuestionsText] = useState(managementQuestions.join("\n"));
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  async function save() {
    setPending(true);
    setError(null);
    try {
      const res = await fetch(`/api/reports/${reportId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          executive_summary: summaryText
            .split("\n")
            .map((s) => s.trim())
            .filter(Boolean),
          management_questions: questionsText
            .split("\n")
            .map((s) => s.trim())
            .filter(Boolean),
        }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(data?.detail || "Save failed");
      }
      router.refresh();
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setPending(false);
    }
  }

  async function rerunAiOnly() {
    setPending(true);
    setError(null);
    try {
      const res = await fetch("/api/reports/regenerate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "ai_only" }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(data?.detail || "AI re-run failed");
      }
      const report = (await res.json()) as { id: string };
      router.push(`/dashboard/reports/${report.id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI re-run failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <Card className="border-dashed">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="text-sm font-semibold text-ribet-text"
      >
        {open ? "Hide narrative editor" : "Edit narrative"}
      </button>
      {open && (
        <div className="mt-4 space-y-4">
          <div>
            <label className="text-xs font-medium text-ribet-muted">Executive summary</label>
            <textarea
              rows={4}
              value={summaryText}
              onChange={(e) => setSummaryText(e.target.value)}
              className="mt-1 w-full rounded-xl border border-ribet-border bg-ribet-card px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-ribet-muted">
              Management questions
            </label>
            <textarea
              rows={4}
              value={questionsText}
              onChange={(e) => setQuestionsText(e.target.value)}
              className="mt-1 w-full rounded-xl border border-ribet-border bg-ribet-card px-3 py-2 text-sm"
            />
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void save()}
              disabled={pending}
              className="rounded-full bg-ribet-green px-4 py-2 text-sm font-medium disabled:opacity-50"
            >
              Save edits
            </button>
            <button
              type="button"
              onClick={() => void rerunAiOnly()}
              disabled={pending}
              className="rounded-full border border-ribet-border px-4 py-2 text-sm font-medium disabled:opacity-50"
            >
              Re-run AI narration
            </button>
            <button
              type="button"
              onClick={() => {
                setSummaryText(executiveSummary.join("\n"));
                setQuestionsText(managementQuestions.join("\n"));
              }}
              className="rounded-full border border-ribet-border px-4 py-2 text-sm font-medium"
            >
              Reset to generated
            </button>
          </div>
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
