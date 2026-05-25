export type UploadStatus =
  | "pending"
  | "uploading"
  | "processing"
  | "done"
  | "error";

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
    consentAcknowledged?: boolean
  ): Promise<UploadFileMeta[]>;
}

export type UploadJob = {
  id: string;
  status: UploadStatus;
  file_name: string;
  sector?: string | null;
  errors?: string[];
  report_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type UploadJobsResponse = {
  jobs: UploadJob[];
};
