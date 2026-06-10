"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function RegenerateReportButton({
  label = "Regenerate report",
}: {
  label?: string;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRegenerate() {
    setPending(true);
    setError(null);
    try {
      const res = await fetch("/api/reports/regenerate", { method: "POST" });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as {
          detail?: string;
        } | null;
        throw new Error(data?.detail || `Regenerate failed (${res.status})`);
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Regenerate failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <button
        type="button"
        onClick={handleRegenerate}
        disabled={pending}
        className="rounded-full bg-ribet-green px-5 py-2.5 text-sm font-medium text-ribet-text hover:opacity-90 disabled:opacity-50"
      >
        {pending ? "Generating…" : label}
      </button>
      {error && (
        <span className="text-xs text-ribet-risk" role="alert">
          {error}
        </span>
      )}
    </span>
  );
}
