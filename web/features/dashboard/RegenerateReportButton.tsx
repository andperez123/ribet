"use client";

import Link from "next/link";

export function RegenerateReportButton({
  label = "Regenerate report",
  useSetup = true,
}: {
  label?: string;
  useSetup?: boolean;
}) {
  if (useSetup) {
    return (
      <Link
        href="/dashboard/reports/setup"
        className="inline-flex rounded-full bg-ribet-green px-5 py-2.5 text-sm font-medium text-ribet-text hover:opacity-90"
      >
        {label}
      </Link>
    );
  }

  return (
    <Link
      href="/dashboard/reports/setup"
      className="inline-flex rounded-full bg-ribet-green px-5 py-2.5 text-sm font-medium text-ribet-text hover:opacity-90"
    >
      {label}
    </Link>
  );
}
