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

export type UploadFileMeta = {
  id: string;
  name: string;
  size: number;
  mimeType: string;
  sector?: UploadSector;
  status: UploadStatus;
  error?: string;
  reportId?: string;
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
  errors?: string[];
  report_id?: string | null;
  mapping_status?: string | null;
  mapping_confidence?: number | null;
  duplicate_of_job_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type UploadJobsResponse = {
  jobs: UploadJob[];
};
