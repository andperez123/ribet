"use client";

import { useCallback, useMemo, useState } from "react";
import type { UploadFileMeta, UploadSector } from "@/lib/types/upload";
import { createUploadClient } from "./upload.client";
import { useUploadMode } from "./useUploadMode";

export function useUpload() {
  const uploadMode = useUploadMode();
  const client = useMemo(
    () => createUploadClient(uploadMode),
    [uploadMode]
  );

  const [files, setFiles] = useState<UploadFileMeta[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastReportId, setLastReportId] = useState<string | null>(null);

  const upload = useCallback(
    async (
      fileList: File[],
      sector: UploadSector,
      consentAcknowledged = false,
      description?: string
    ) => {
      if (!fileList.length) return;
      setIsUploading(true);
      setError(null);

      try {
        const results = await client.upload(
          fileList,
          sector,
          consentAcknowledged,
          description
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

  return {
    files,
    setFiles,
    upload,
    isUploading,
    error,
    clear,
    lastReportId,
    setLastReportId,
  };
}
