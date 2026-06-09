"use client";

import { CheckCircle, Circle, Loader2 } from "lucide-react";
import type { IngestJobRecord } from "@/lib/types/report";

const STAGE_ORDER = [
  "pending",
  "transform",
  "rules",
  "evidence_pack",
  "ai_analyst",
  "verification",
  "report_ready",
  "needs_review",
  "error",
] as const;

function stageIndex(stage: string | null | undefined): number {
  if (!stage) return 0;
  const idx = STAGE_ORDER.indexOf(stage as (typeof STAGE_ORDER)[number]);
  return idx >= 0 ? idx : 0;
}

function stepState(
  stepStage: string,
  currentStage: string | null | undefined,
  jobStatus: IngestJobRecord["status"] | "uploading"
): "done" | "running" | "pending" {
  if (jobStatus === "done") return "done";
  if (jobStatus === "error") return "pending";
  if (jobStatus === "needs_review" && stepStage === "transform") return "running";

  const currentIdx = stageIndex(
    currentStage ??
      (jobStatus === "processing" || jobStatus === "uploading" ? "transform" : "pending")
  );
  const stepIdx = STAGE_ORDER.indexOf(stepStage as (typeof STAGE_ORDER)[number]);
  const mappedStepIdx =
    stepStage === "transform"
      ? STAGE_ORDER.indexOf("transform")
      : stepIdx >= 0
        ? stepIdx
        : 0;

  if (currentIdx > mappedStepIdx) return "done";
  if (currentIdx === mappedStepIdx) return "running";
  return "pending";
}

export function PipelineProgressBar({
  job,
}: {
  job: {
    id: string;
    status: IngestJobRecord["status"] | "uploading";
    file_name: string;
    pipeline_stage?: IngestJobRecord["pipeline_stage"];
  };
}) {
  if (
    !job.pipeline_stage &&
    job.status !== "processing" &&
    job.status !== "uploading"
  ) {
    return null;
  }

  const displayStages = [
    { stage: "transform", label: "Ingest" },
    { stage: "transform", label: "Normalize" },
    { stage: "rules", label: "Brain 1" },
    { stage: "evidence_pack", label: "Evidence Pack" },
    { stage: "ai_analyst", label: "Brain 2" },
    { stage: "verification", label: "Verify" },
    { stage: "report_ready", label: "Report" },
  ];

  return (
    <div className="mt-3 space-y-2">
      <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
        Pipeline
      </p>
      <div className="flex flex-wrap items-center gap-1">
        {displayStages.map((step, i) => {
          const state = stepState(step.stage, job.pipeline_stage, job.status);
          return (
            <div key={`${step.label}-${i}`} className="flex items-center gap-1">
              {state === "done" ? (
                <CheckCircle className="h-3.5 w-3.5 text-ribet-green" />
              ) : state === "running" ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-ribet-green" />
              ) : (
                <Circle className="h-3.5 w-3.5 text-ribet-muted/50" />
              )}
              <span
                className={`text-[10px] ${
                  state === "running"
                    ? "font-medium text-ribet-text"
                    : state === "done"
                      ? "text-ribet-muted"
                      : "text-ribet-muted/60"
                }`}
              >
                {step.label}
              </span>
              {i < displayStages.length - 1 && (
                <span className="mx-1 text-ribet-muted/40">→</span>
              )}
            </div>
          );
        })}
      </div>
      {job.pipeline_stage && (
        <p className="text-[10px] text-ribet-muted">Stage: {job.pipeline_stage}</p>
      )}
    </div>
  );
}
