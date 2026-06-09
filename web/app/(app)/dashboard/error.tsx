"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[dashboard]", error);
  }, [error]);

  return (
    <div className="mx-auto max-w-lg space-y-4 py-12 text-center">
      <h1 className="text-xl font-semibold text-ribet-text">
        Dashboard could not load
      </h1>
      <p className="text-sm text-ribet-muted">
        We could not reach the Ribet API. Check your connection and try again.
        If this keeps happening, confirm the API service is running and your
        account is signed in.
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <button
          type="button"
          onClick={() => reset()}
          className="rounded-full bg-ribet-green px-5 py-2.5 text-sm font-medium text-ribet-text"
        >
          Try again
        </button>
        <Link
          href="/dashboard/upload"
          className="rounded-full border border-ribet-border px-5 py-2.5 text-sm font-medium text-ribet-text"
        >
          Upload files
        </Link>
        <Link
          href="/"
          className="rounded-full border border-ribet-border px-5 py-2.5 text-sm font-medium text-ribet-text"
        >
          Back to home
        </Link>
      </div>
    </div>
  );
}
