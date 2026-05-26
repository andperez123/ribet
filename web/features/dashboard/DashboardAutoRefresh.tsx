"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

/** Refresh dashboard while jobs are processing so reports appear without manual reload. */
export function DashboardAutoRefresh({ active }: { active: boolean }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const processingHint = searchParams.get("processing");

  useEffect(() => {
    if (!active && !processingHint) return;

    const id = setInterval(() => {
      router.refresh();
    }, 5000);

    return () => clearInterval(id);
  }, [active, processingHint, router]);

  return null;
}
