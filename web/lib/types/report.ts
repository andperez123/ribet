export type Severity = "low" | "medium" | "high" | "critical" | string;

export type ReportFinding = {
  finding_type?: string;
  title: string;
  detail?: string;
  severity?: Severity;
  confidence?: number;
  business_impact?: string;
  department?: string;
  category?: string;
  suggested_action?: string;
  fingerprint?: string;
};

export type OperationalReport = {
  id: string;
  org_id: string;
  executive_summary: string[];
  financial_findings: ReportFinding[];
  operational_findings: ReportFinding[];
  risk_areas: ReportFinding[];
  suggested_actions: string[];
  trend_snapshot: string[];
  health_score: number;
  health_status: string;
  generated_at: string;
};

export type Finding = {
  id: string;
  finding_type: string;
  title: string;
  detail: string;
  severity: Severity;
  confidence: number;
  business_impact: string;
  department: string;
  category: string;
  suggested_action: string | null;
  detected_at: string;
};

export type HealthScore = {
  score: number;
  status: string;
  components: Record<string, number>;
  computed_at: string | null;
};

export type HealthHistory = {
  snapshots: HealthScore[];
};

export type WeeklyBrief = {
  org_id: string;
  period: string;
  sections: Record<string, string[]>;
};

export type IngestJobRecord = {
  id: string;
  status: "pending" | "processing" | "done" | "error";
  file_name: string;
  sector?: string | null;
  errors?: string[];
  report_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type IngestJobsResponse = {
  jobs: IngestJobRecord[];
};
