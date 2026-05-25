"use client";

import { useCallback, useMemo, useState } from "react";
import { getEnv } from "@/lib/config/env";
import type { UploadFileMeta, UploadSector } from "@/lib/types/upload";
import { createUploadClient } from "./upload.client";

export function useUpload() {
  const client = useMemo(
    () => createUploadClient(getEnv().NEXT_PUBLIC_UPLOAD_MODE),
    []
  );

  const [files, setFiles] = useState<UploadFileMeta[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastReportId, setLastReportId] = useState<string | null>(null);

  const upload = useCallback(
    async (
      fileList: File[],
      sector: UploadSector,
      consentAcknowledged = false
    ) => {
      if (!fileList.length) return;
      setIsUploading(true);
      setError(null);

      try {
        const results = await client.upload(
          fileList,
          sector,
          consentAcknowledged
        );
        setFiles((prev) => [...prev, ...results]);
        const reportId = [...results]
          .reverse()
          .find((f) => f.reportId)?.reportId;
        if (reportId) setLastReportId(reportId);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setIsUploading(false);
      }
    },
    [client]
  );

  const clear = useCallback(() => {
    setFiles([]);
    setError(null);
    setLastReportId(null);
  }, []);

  return { files, upload, isUploading, error, clear, lastReportId };
}
