"use client";

import { useCallback, useEffect, useRef } from "react";
import type { UploadFileMeta } from "@/lib/types/upload";
import { firstJobError } from "@/lib/upload/job-errors";
import { ApiUploadClient, createUploadClient } from "./upload.client";
import { useUploadMode } from "./useUploadMode";

export function useJobPolling(
  files: UploadFileMeta[],
  setFiles: React.Dispatch<React.SetStateAction<UploadFileMeta[]>>,
  onReportReady?: (reportId: string) => void
) {
  const uploadMode = useUploadMode();
  const clientRef = useRef(createUploadClient(uploadMode));
  clientRef.current = createUploadClient(uploadMode);

  const poll = useCallback(async () => {
    const client = clientRef.current;
    if (!("pollJob" in client)) return;

    const pending = files.filter(
      (f) =>
        f.status === "processing" ||
        f.status === "uploading"
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
            error: firstJobError(job.errors) ?? undefined,
            intakeMetadata: job.intake_metadata ?? undefined,
            pipelineStage: job.pipeline_stage ?? undefined,
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
          intakeMetadata: u.intakeMetadata ?? f.intakeMetadata,
          pipelineStage: u.pipelineStage ?? f.pipelineStage,
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
