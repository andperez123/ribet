export type AdminJobFailure = {
  event_id: string;
  created_at: string;
  org_id: string | null;
  org_name: string | null;
  job_id: string | null;
  file_name: string | null;
  sector: string | null;
  error_code: string | null;
  error_message: string | null;
  error_detail: string | null;
  intake_metadata: Record<string, unknown> | null;
  job_errors: Array<{
    code: string;
    message: string;
    hint?: string | null;
    detail?: string | null;
  }>;
  job_status: string | null;
};

export type AdminJobFailuresResponse = {
  failures: AdminJobFailure[];
  total: number;
};
