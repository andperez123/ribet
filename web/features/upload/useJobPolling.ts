"use client";

import { useCallback, useEffect, useRef } from "react";
import type { UploadFileMeta } from "@/lib/types/upload";
import { ApiUploadClient, createUploadClient } from "./upload.client";
import { getEnv } from "@/lib/config/env";

export function useJobPolling(
  files: UploadFileMeta[],
  setFiles: React.Dispatch<React.SetStateAction<UploadFileMeta[]>>,
  onReportReady?: (reportId: string) => void
) {
  const clientRef = useRef(
    createUploadClient(getEnv().NEXT_PUBLIC_UPLOAD_MODE)
  );

  const poll = useCallback(async () => {
    const client = clientRef.current;
    if (!("pollJob" in client)) return;

    const pending = files.filter(
      (f) => f.status === "processing" || f.status === "uploading"
    );
    if (!pending.length) return;

    const updates = await Promise.all(
      pending.map(async (f) => {
        try {
          const job = await (client as ApiUploadClient).pollJob(f.id);
          return {
            id: f.id,
            status:
              job.status === "pending" ? "processing" : job.status,
            reportId: job.report_id ?? undefined,
            error: job.errors?.[0],
          };
        } catch {
          return null;
        }
      })
    );

    setFiles((prev) =>
      prev.map((f) => {
        const u = updates.find((x) => x?.id === f.id);
        if (!u) return f;
        return {
          ...f,
          status: u.status,
          reportId: u.reportId ?? f.reportId,
          error: u.error,
        };
      })
    );

    const reportId = updates.find((u) => u?.reportId)?.reportId;
    if (reportId) onReportReady?.(reportId);
  }, [files, setFiles, onReportReady]);

  useEffect(() => {
    const active = files.some(
      (f) => f.status === "processing" || f.status === "uploading"
    );
    if (!active) return;

    poll();
    const id = setInterval(poll, 2000);
    return () => clearInterval(id);
  }, [files, poll]);
}
