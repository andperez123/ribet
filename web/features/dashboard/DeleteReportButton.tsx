"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function DeleteReportButton({
  reportId,
  label = "Delete",
  redirectTo,
}: {
  reportId: string;
  label?: string;
  redirectTo?: string;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    const confirmed = window.confirm(
      "Delete this report? This cannot be undone."
    );
    if (!confirmed) return;

    setPending(true);
    setError(null);
    try {
      const res = await fetch(`/api/reports/${reportId}`, { method: "DELETE" });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as {
          detail?: string;
        } | null;
        throw new Error(data?.detail || `Delete failed (${res.status})`);
      }
      if (redirectTo) {
        router.push(redirectTo);
        router.refresh();
      } else {
        router.refresh();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <button
        type="button"
        onClick={handleDelete}
        disabled={pending}
        className="font-medium text-red-600 hover:underline disabled:opacity-50"
      >
        {pending ? "Deleting…" : label}
      </button>
      {error && (
        <span className="text-xs text-red-600" role="alert">
          {error}
        </span>
      )}
    </span>
  );
}
