"use client";

import {
  Upload,
  CheckCircle,
  Loader2,
  DollarSign,
  Factory,
  ClipboardList,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useRef, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { uploadSection } from "@/lib/content/landing";
import {
  SECTORS,
  DEFAULT_SECTOR,
  type SectorId,
} from "@/lib/sectors";
import type { UploadSector } from "@/lib/types/upload";
import { useUpload } from "./useUpload";

const SECTOR_ICONS: Record<SectorId, typeof DollarSign> = {
  financials: DollarSign,
  manufacturing: Factory,
  orders: ClipboardList,
  sales: TrendingUp,
};

export function SectorUploadFlow() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [activeSector, setActiveSector] = useState<SectorId>(DEFAULT_SECTOR);
  const [isDragging, setIsDragging] = useState(false);
  const { files, upload, isUploading, error, clear, lastReportId } = useUpload();

  const activeDef = SECTORS.find((s) => s.id === activeSector)!;

  const handleFiles = useCallback(
    (list: FileList | null) => {
      if (!list?.length) return;
      upload(Array.from(list), activeSector as UploadSector);
    },
    [upload, activeSector]
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const doneCount = files.filter((f) => f.status === "done").length;

  return (
    <div className="w-full">
      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        {SECTORS.map((sector) => {
          const Icon = SECTOR_ICONS[sector.id];
          const selected = activeSector === sector.id;
          return (
            <button
              key={sector.id}
              type="button"
              onClick={() => setActiveSector(sector.id)}
              className={`rounded-xl border px-4 py-3 text-left transition-colors ${
                selected
                  ? "border-rivet-green bg-rivet-green/10"
                  : "border-rivet-border bg-rivet-card hover:border-rivet-green/40"
              }`}
            >
              <Icon
                className={`h-5 w-5 ${selected ? "text-rivet-green" : "text-rivet-muted"}`}
              />
              <p className="mt-2 text-sm font-semibold text-rivet-text">
                {sector.label}
              </p>
            </button>
          );
        })}
      </div>

      <p className="mb-4 text-center text-sm text-rivet-muted">
        {activeDef.description}{" "}
        <span className="text-rivet-text/80">({activeDef.examples})</span>
      </p>

      <div
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        className={`flex min-h-[200px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed bg-rivet-card px-8 py-14 transition-colors md:min-h-[220px] ${
          isDragging
            ? "border-rivet-green bg-rivet-green/5"
            : "border-rivet-border hover:border-rivet-green/50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={uploadSection.accepted}
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        {isUploading ? (
          <Loader2 className="h-10 w-10 animate-spin text-rivet-green" />
        ) : (
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-rivet-green/15">
            <Upload className="h-7 w-7 text-rivet-green" />
          </div>
        )}

        <p className="mt-5 text-lg font-semibold text-rivet-text">
          Upload to {activeDef.label}
        </p>
        <p className="mt-1 text-sm text-rivet-muted">
          {uploadSection.boxSubtitle}
        </p>
      </div>

      <p className="mt-4 text-center text-xs text-rivet-muted">
        {uploadSection.helper} Upload across sectors to unlock logistics insights
        on your dashboard.
      </p>

      {error && (
        <p className="mt-3 text-center text-sm text-rivet-risk">{error}</p>
      )}

      {files.length > 0 && (
        <div className="mt-6 space-y-2">
          {files.map((f) => (
            <div
              key={f.id}
              className="flex items-center gap-3 rounded-lg border border-rivet-border bg-rivet-card px-4 py-3 text-sm"
            >
              {f.status === "done" ? (
                <CheckCircle className="h-4 w-4 shrink-0 text-rivet-green" />
              ) : (
                <Loader2 className="h-4 w-4 shrink-0 animate-spin text-rivet-green" />
              )}
              <span className="flex-1 truncate">{f.name}</span>
              {f.sector && (
                <Badge variant="muted" className="capitalize">
                  {f.sector}
                </Badge>
              )}
              <span className="text-xs capitalize text-rivet-muted">
                {f.status}
              </span>
            </div>
          ))}
          {doneCount > 0 && (
            <div className="flex flex-wrap items-center gap-4">
              {lastReportId && (
                <Link
                  href={`/dashboard/reports/${lastReportId}`}
                  className="rounded-full bg-rivet-green px-4 py-2 text-sm font-medium text-rivet-text hover:opacity-90"
                >
                  View report
                </Link>
              )}
              <Link
                href="/dashboard"
                className="text-sm font-medium text-rivet-muted hover:text-rivet-text"
              >
                Open dashboard
              </Link>
              <button
                type="button"
                onClick={clear}
                className="text-xs text-rivet-muted underline hover:text-rivet-text"
              >
                Clear
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
