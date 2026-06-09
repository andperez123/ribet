export type UploadStatus =
  | "pending"
  | "uploading"
  | "processing"
  | "done"
  | "error"
  | "needs_review";

export type UploadSector =
  | "financials"
  | "manufacturing"
  | "orders"
  | "sales";

export type PipelineStage =
  | "pending"
  | "transform"
  | "rules"
  | "evidence_pack"
  | "ai_analyst"
  | "verification"
  | "report_ready"
  | "needs_review"
  | "error";

export type UploadFileMeta = {
  id: string;
  name: string;
  size: number;
  mimeType: string;
  sector?: UploadSector;
  status: UploadStatus;
  error?: import("@/lib/upload/job-errors").JobError;
  reportId?: string;
  intakeMetadata?: import("@/lib/upload/job-errors").IntakeMetadata | null;
  pipelineStage?: PipelineStage | null;
};

export interface UploadClient {
  upload(
    files: File[],
    sector: UploadSector,
    consentAcknowledged?: boolean,
    description?: string
  ): Promise<UploadFileMeta[]>;
}

export type UploadJob = {
  id: string;
  status: UploadStatus | "pending";
  file_name: string;
  sector?: string | null;
  errors?: Array<
    | string
    | {
        code: string;
        message: string;
        hint?: string | null;
        detail?: string | null;
      }
  >;
  report_id?: string | null;
  mapping_status?: string | null;
  mapping_confidence?: number | null;
  duplicate_of_job_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  intake_metadata?: import("@/lib/upload/job-errors").IntakeMetadata | null;
  pipeline_stage?: PipelineStage | null;
};

export type UploadJobsResponse = {
  jobs: UploadJob[];
};
