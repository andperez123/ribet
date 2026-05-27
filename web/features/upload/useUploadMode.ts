"use client";

import { useEffect, useState } from "react";
import { getEnv } from "@/lib/config/env";

/** Resolves upload mode at runtime (Railway sets env after build). */
export function useUploadMode(): "mock" | "api" {
  const buildDefault = getEnv().NEXT_PUBLIC_UPLOAD_MODE;
  const [mode, setMode] = useState<"mock" | "api">(buildDefault);

  useEffect(() => {
    fetch("/api/config/public", { cache: "no-store" })
      .then((r) => r.json())
      .then((data: { uploadMode?: string }) => {
        if (data.uploadMode === "mock" || data.uploadMode === "api") {
          setMode(data.uploadMode);
        }
      })
      .catch(() => {
        /* keep build-time default */
      });
  }, []);

  return mode;
}
