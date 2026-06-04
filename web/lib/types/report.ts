export type Severity = "low" | "medium" | "high" | "critical" | string;

export type InsightSeverity = "info" | "watch" | "alert";

export type TopEntry = {
  label: string;
  amount: number;
  pct: number;
  detail?: string;
};

export type DataDigest = {
  ar_total: number;
  ar_over_90: number;
  ar_over_90_pct: number;
  ar_invoice_count: number;
  top_customers: TopEntry[];

  ap_total: number;
  ap_negative_total: number;
  vendor_count: number;
  top_vendors: TopEntry[];

  gl_txn_count: number;
  gl_adjustment_total: number;
  gl_unmapped_count: number;

  inventory_item_count: number;
  inventory_total_qty: number;
  inventory_negative_count: number;
  inventory_zero_count: number;
  inventory_orphan_count: number;
};

export type DomainInsight = {
  domain: string;
  title: string;
  body: string;
  severity: InsightSeverity;
  metric_label?: string | null;
  metric_value?: string | null;
  finding_type?: string | null;
};

export type DataCoverage = {
  ar: boolean;
  ap: boolean;
  gl: boolean;
  inventory: boolean;
};

export type AnalysisMetadata = {
  narration: "completed" | "skipped" | "failed" | "legacy";
  model?: string | null;
  finding_count: number;
  narrated_count: number;
  data_domains_present: string[];
  duration_ms?: number | null;
};

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
  narrative?: string | null;
  recommendation?: string | null;
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
  data_digest?: DataDigest;
  domain_insights?: DomainInsight[];
  data_coverage?: DataCoverage;
  analysis_metadata?: AnalysisMetadata;
  analyst_summary?: string | null;
  management_questions?: string[];
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
  narrative?: string | null;
  recommendation?: string | null;
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

export type ReportListItem = {
  id: string;
  generated_at: string;
  health_score: number;
  health_status: string;
  finding_count: number;
};

export type ReportsListResponse = {
  reports: ReportListItem[];
};
