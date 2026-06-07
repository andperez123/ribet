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
import { AsyncWorkflowBanner } from "@/components/ui/AsyncWorkflowBanner";
import { Badge } from "@/components/ui/Badge";
import { asyncWorkflow } from "@/lib/content/asyncWorkflow";
import { uploadSection } from "@/lib/content/landing";
import {
  SECTORS,
  DEFAULT_SECTOR,
  type SectorId,
} from "@/lib/sectors";
import type { UploadSector } from "@/lib/types/upload";
import { MappingReviewPanel } from "./MappingReviewPanel";
import { useJobPolling } from "./useJobPolling";
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
  const [consent, setConsent] = useState(false);
  const [consentError, setConsentError] = useState<string | null>(null);
  const [description, setDescription] = useState("");
  const [filesConfirmed, setFilesConfirmed] = useState(false);
  const {
    files,
    setFiles,
    upload,
    isUploading,
    error,
    clear,
    lastReportId,
    setLastReportId,
  } = useUpload();

  useJobPolling(files, setFiles, (reportId) => {
    if (reportId) setLastReportId(reportId);
  });

  const activeDef = SECTORS.find((s) => s.id === activeSector)!;

  const handleFiles = useCallback(
    (list: FileList | null) => {
      if (!list?.length) return;
      if (!consent) {
        setConsentError(asyncWorkflow.consentRequired);
        return;
      }
      setConsentError(null);
      setFilesConfirmed(false);
      upload(
        Array.from(list),
        activeSector as UploadSector,
        consent,
        description
      ).then(() => setFilesConfirmed(true));
    },
    [upload, activeSector, consent, description]
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const doneCount = files.filter((f) => f.status === "done").length;
  const processingCount = files.filter(
    (f) => f.status === "processing" || f.status === "uploading"
  ).length;
  const showUploadBanner =
    filesConfirmed && files.length > 0 && processingCount + doneCount > 0;

  return (
    <div className="w-full">
      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        {SECTORS.map((sector) => {
          const Icon = SECTOR_ICONS[sector.id];
          const selected = activeSector === sector.id;
          const disabled = sector.comingSoon === true;
          return (
            <button
              key={sector.id}
              type="button"
              disabled={disabled}
              onClick={() => {
                if (!disabled) setActiveSector(sector.id);
              }}
              className={`rounded-xl border px-4 py-3 text-left transition-colors ${
                disabled
                  ? "cursor-not-allowed border-ribet-border/60 bg-ribet-card/40 opacity-60"
                  : selected
                    ? "border-ribet-green bg-ribet-green/10"
                    : "border-ribet-border bg-ribet-card hover:border-ribet-green/40"
              }`}
            >
              <Icon
                className={`h-5 w-5 ${selected && !disabled ? "text-ribet-green" : "text-ribet-muted"}`}
              />
              <p className="mt-2 text-sm font-semibold text-ribet-text">
                {sector.label}
              </p>
              {disabled && (
                <Badge variant="muted" className="mt-2 text-[10px]">
                  Coming soon
                </Badge>
              )}
            </button>
          );
        })}
      </div>

      <p className="mb-4 text-center text-sm text-ribet-muted">
        {activeDef.description}{" "}
        <span className="text-ribet-text/80">({activeDef.examples})</span>
      </p>

      {showUploadBanner && (
        <AsyncWorkflowBanner
          className="mb-6"
          title={asyncWorkflow.upload.title}
          body={asyncWorkflow.upload.body}
        />
      )}

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
        className={`flex min-h-[200px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed bg-ribet-card px-8 py-14 transition-colors md:min-h-[220px] ${
          isDragging
            ? "border-ribet-green bg-ribet-green/5"
            : "border-ribet-border hover:border-ribet-green/50"
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
          <Loader2 className="h-10 w-10 animate-spin text-ribet-green" />
        ) : (
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-ribet-green/15">
            <Upload className="h-7 w-7 text-ribet-green" />
          </div>
        )}

        <p className="mt-5 text-lg font-semibold text-ribet-text">
          Upload to {activeDef.label}
        </p>
        <p className="mt-1 text-sm text-ribet-muted">
          {uploadSection.boxSubtitle}
        </p>
      </div>

      <label className="mt-4 block text-center text-sm text-ribet-muted">
        <span className="mb-1 block">Describe this data (optional)</span>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={500}
          rows={2}
          placeholder="e.g. Q2 AR aging from JobBOSS"
          className="w-full max-w-md rounded-lg border border-ribet-border bg-ribet-card px-3 py-2 text-sm text-ribet-text"
        />
      </label>

      <label className="mt-4 flex cursor-pointer items-start justify-center gap-2 text-left text-sm text-ribet-muted">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => {
            setConsent(e.target.checked);
            if (e.target.checked) setConsentError(null);
          }}
          className="mt-1"
        />
        <span>
          I confirm I have authority to upload this data and agree to the{" "}
          <a href="/legal/terms" className="text-ribet-green hover:underline">
            Terms
          </a>{" "}
          and{" "}
          <a href="/legal/privacy" className="text-ribet-green hover:underline">
            Privacy Policy
          </a>
          .
        </span>
      </label>

      {consentError && (
        <p className="mt-2 text-center text-sm text-ribet-risk" role="alert">
          {consentError}
        </p>
      )}

      <p className="mt-2 text-center text-xs text-ribet-muted">
        {uploadSection.helper} Upload across sectors to unlock logistics insights
        on your dashboard.
      </p>

      {error && (
        <p className="mt-3 text-center text-sm text-ribet-risk">{error}</p>
      )}

      {files.some((f) => f.status === "needs_review") && (
        <div className="mt-6 space-y-3">
          {files
            .filter((f) => f.status === "needs_review")
            .map((f) => (
              <MappingReviewPanel
                key={f.id}
                jobId={f.id}
                fileName={f.name}
                onConfirmed={(reportId) => {
                  setLastReportId(reportId);
                  setFiles((prev) =>
                    prev.map((x) =>
                      x.id === f.id
                        ? { ...x, status: "done", reportId }
                        : x
                    )
                  );
                }}
              />
            ))}
        </div>
      )}

      {files.length > 0 && (
        <div className="mt-6 space-y-2">
          {files.map((f) => (
            <div
              key={f.id}
              className="flex items-center gap-3 rounded-lg border border-ribet-border bg-ribet-card px-4 py-3 text-sm"
            >
              {f.status === "done" ? (
                <CheckCircle className="h-4 w-4 shrink-0 text-ribet-green" />
              ) : f.status === "error" ? (
                <span className="text-ribet-risk text-xs">!</span>
              ) : f.status === "needs_review" ? (
                <span className="text-amber-400 text-xs">?</span>
              ) : (
                <Loader2 className="h-4 w-4 shrink-0 animate-spin text-ribet-green" />
              )}
              <span className="flex-1 truncate">{f.name}</span>
              {f.sector && (
                <Badge variant="muted" className="capitalize">
                  {f.sector}
                </Badge>
              )}
              <span className="text-xs capitalize text-ribet-muted">
                {f.status === "processing" ? "processing" : f.status}
              </span>
            </div>
          ))}
          <div className="flex flex-wrap items-center gap-4">
            {(lastReportId ||
              files.find((f) => f.reportId)?.reportId) && (
              <Link
                href={`/dashboard/reports/${lastReportId ?? files.find((f) => f.reportId)?.reportId}`}
                className="rounded-full bg-ribet-green px-4 py-2 text-sm font-medium text-ribet-text hover:opacity-90"
              >
                View report
              </Link>
            )}
            <Link
              href="/dashboard"
              className="text-sm font-medium text-ribet-muted hover:text-ribet-text"
            >
              Open dashboard
            </Link>
            <button
              type="button"
              onClick={() => {
                clear();
                setFilesConfirmed(false);
              }}
              className="text-xs text-ribet-muted underline hover:text-ribet-text"
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
