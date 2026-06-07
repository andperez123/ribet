"use client";

import { AlertCircle } from "lucide-react";
import type { JobError } from "@/lib/upload/job-errors";
import type { IntakeMetadata } from "@/lib/upload/job-errors";

export function UploadJobErrorPanel({
  fileName,
  jobId,
  error,
  intakeMetadata,
  compact = false,
}: {
  fileName?: string;
  jobId?: string;
  error: JobError;
  intakeMetadata?: IntakeMetadata | null;
  compact?: boolean;
}) {
  return (
    <div
      className={`rounded-lg border border-ribet-risk/30 bg-ribet-risk/5 ${
        compact ? "px-3 py-2" : "px-4 py-3"
      }`}
      role="alert"
    >
      <div className="flex gap-2">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-ribet-risk" />
        <div className="min-w-0 flex-1 space-y-2">
          <div>
            {fileName && (
              <p className="truncate text-xs font-medium text-ribet-muted">
                {fileName}
              </p>
            )}
            <p className={`font-medium text-ribet-text ${compact ? "text-sm" : ""}`}>
              {error.message}
            </p>
            {error.hint && (
              <p className="mt-1 text-sm text-ribet-muted">{error.hint}</p>
            )}
          </div>

          <details className="text-xs text-ribet-muted">
            <summary className="cursor-pointer font-medium text-ribet-text/80 hover:text-ribet-text">
              Technical details
            </summary>
            <dl className="mt-2 space-y-1 rounded-md bg-ribet-card/60 p-3 font-mono text-[11px] leading-relaxed">
              {jobId && (
                <div>
                  <dt className="inline text-ribet-muted">Job ID: </dt>
                  <dd className="inline break-all text-ribet-text">{jobId}</dd>
                </div>
              )}
              <div>
                <dt className="inline text-ribet-muted">Code: </dt>
                <dd className="inline text-ribet-text">{error.code}</dd>
              </div>
              {error.detail && error.detail !== error.message && (
                <div>
                  <dt className="text-ribet-muted">Detail</dt>
                  <dd className="mt-0.5 whitespace-pre-wrap break-words text-ribet-text">
                    {error.detail}
                  </dd>
                </div>
              )}
              {intakeMetadata && (
                <>
                  {intakeMetadata.sheet_name && (
                    <div>
                      <dt className="inline text-ribet-muted">Excel sheet: </dt>
                      <dd className="inline text-ribet-text">
                        {intakeMetadata.sheet_name}
                      </dd>
                    </div>
                  )}
                  {intakeMetadata.encoding && (
                    <div>
                      <dt className="inline text-ribet-muted">Encoding: </dt>
                      <dd className="inline text-ribet-text">
                        {intakeMetadata.encoding}
                      </dd>
                    </div>
                  )}
                  {(intakeMetadata.skipped_rows ?? 0) > 0 && (
                    <div>
                      <dt className="inline text-ribet-muted">Header row: </dt>
                      <dd className="inline text-ribet-text">
                        row {(intakeMetadata.header_row_index ?? 0) + 1}{" "}
                        (skipped {intakeMetadata.skipped_rows} preamble row
                        {(intakeMetadata.skipped_rows ?? 0) === 1 ? "" : "s"})
                      </dd>
                    </div>
                  )}
                  {intakeMetadata.warnings?.map((w) => (
                    <div key={w}>
                      <dt className="inline text-ribet-muted">Warning: </dt>
                      <dd className="inline text-ribet-text">{w}</dd>
                    </div>
                  ))}
                </>
              )}
            </dl>
            <p className="mt-2 text-[11px] text-ribet-muted">
              Share the job ID with support if you need help. Check worker logs for{" "}
              <code className="text-ribet-text">job_failed</code> events.
            </p>
          </details>
        </div>
      </div>
    </div>
  );
}
