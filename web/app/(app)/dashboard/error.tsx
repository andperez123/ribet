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
        The app could not reach the API. On Railway, check the{" "}
        <strong>web</strong> service: <code className="text-xs">FASTAPI_URL</code>{" "}
        (private <code className="text-xs">ribet_api</code> reference or temporary{" "}
        <code className="text-xs">https://api.ribetlab.com</code>) and that{" "}
        <code className="text-xs">FASTAPI_API_KEY</code> matches API{" "}
        <code className="text-xs">API_KEY</code>, then redeploy web.
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
          href="/"
          className="rounded-full border border-ribet-border px-5 py-2.5 text-sm font-medium text-ribet-text"
        >
          Back to home
        </Link>
      </div>
    </div>
  );
}
