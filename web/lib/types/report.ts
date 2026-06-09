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
  ap_current: number;
  ap_1_30: number;
  ap_31_60: number;
  ap_61_90: number;
  ap_91_plus: number;
  ap_over_60_pct: number;

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
  source_label?: string | null;
};

export type SignalTrace = {
  upload_label?: string;
  period?: string;
  row_count?: number;
  job_id?: string | null;
  report_type?: string | null;
  finding_id?: string | null;
  metric_keys?: string[];
  evidence_verified?: boolean;
};

export type TopSignal = {
  kind: "finding" | "insight" | "executive";
  title: string;
  body: string;
  severity: string;
  why_it_matters?: string;
  metric_label?: string;
  metric_value?: string;
  suggested_action?: string;
  source?: string;
  finding_id?: string | null;
  source_trace?: SignalTrace | null;
};

export type BlockedAnalysis = {
  analysis_name: string;
  reason: string;
  requires_uploads: string[];
};

export type EvidenceSummarySource = {
  label: string;
  detail: string;
};

export type EvidenceSummary = {
  schema_version: string;
  generated_at?: string | null;
  metric_count: number;
  finding_count: number;
  coverage_domains: number;
  confidence_score?: number | null;
  rules_executed: number;
  sources: EvidenceSummarySource[];
};

export type AgentRosterEntry = {
  agent: string;
  domain_scope: string;
  status: "running" | "complete" | "needs_data" | "locked";
  status_message: string;
  last_completed_at?: string | null;
  analysis_duration_ms?: number | null;
  evidence_pack_version?: string | null;
};

export type UnlocksFromUpload = {
  unlocked: ReportUnlock[];
  still_gated: ReportUnlock[];
};

export type ActionItem = {
  title: string;
  detail?: string;
  severity: string;
  suggested_action?: string;
  gap_recommendation?: string;
  finding_type?: string;
};

export type SourceTraceability = {
  upload_label: string;
  period: string;
  row_count: number;
  job_id?: string | null;
  report_type?: string | null;
  finding_id?: string | null;
  metric_keys?: string[];
  evidence_verified?: boolean;
};

export type ReportUnlock = {
  type: string;
  message: string;
};

export type ConfidenceScore = {
  before: number;
  after: number;
  delta: number;
};

export type CoverageDelta = {
  upload_label: string;
  message: string;
};

export type PrimaryAnalysis = {
  triggered_by: string[];
  digest?: DataDigest;
  domain_insights?: DomainInsight[];
  source_traceability?: SourceTraceability;
};

export type OrgWideSynthesis = {
  org_context_domains: string[];
  digest?: DataDigest;
  synthesis_insights?: DomainInsight[];
  cross_domain_findings?: ReportFinding[];
};

export type ReportContract = {
  top_signals?: TopSignal[];
  action_items?: ActionItem[];
  digest_kpis?: DataDigest;
  domain_insights?: DomainInsight[];
  primary_analysis?: PrimaryAnalysis;
  org_wide_synthesis?: OrgWideSynthesis | null;
  coverage_gaps?: Array<{
    gap_type: string;
    reason: string;
    recommended_uploads?: string[];
  }>;
  unlocks_from_this_upload?: ReportUnlock[] | UnlocksFromUpload;
  blocked_analyses?: BlockedAnalysis[];
  evidence_summary?: EvidenceSummary;
  agent_roster?: AgentRosterEntry[];
  source_traceability?: SourceTraceability;
  confidence_score?: ConfidenceScore;
  coverage_delta?: CoverageDelta | null;
};

export type DataCoverage = {
  ar: boolean;
  ap: boolean;
  gl: boolean;
  inventory: boolean;
  ar_present?: boolean;
  ar_unmapped?: boolean;
  ap_aging_available?: boolean;
  primary_domain?: string | null;
};

export type AnalysisMetadata = {
  narration: "completed" | "skipped" | "failed" | "legacy" | "fallback";
  model?: string | null;
  finding_count: number;
  narrated_count: number;
  data_domains_present: string[];
  duration_ms?: number | null;
  insights_source?: string | null;
  verification_status?: string | null;
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
  period_label?: string | null;
  improvement_notes?: ImprovementNote[];
  report_contract?: ReportContract;
  evidence_pack?: Record<string, unknown> | null;
  analyst_output?: AnalystOutput | null;
};

export type TopRisk = {
  rank: number;
  title: string;
  impact: string;
  finding_ids: string[];
  metric_keys: string[];
  narrative: string;
  recommended_action: string;
};

export type ManagementQuestion = {
  question: string;
  context: string;
  finding_ids?: string[];
};

export type AnalystOutput = {
  schema_version: string;
  executive_summary: string[];
  top_risks: TopRisk[];
  management_questions: ManagementQuestion[];
  dashboard_explanations?: {
    ar_risk?: string;
    cash_flow?: string;
    inventory?: string;
    data_quality?: string;
  };
  confidence_notes?: string[];
  recommended_uploads?: Array<{
    upload: string;
    priority: string;
    rationale: string;
    reason_code?: string;
  }>;
  conditional_insights?: Array<{
    locked_capability: string;
    requires_upload: string;
    insight: string;
  }>;
  source?: string;
};

export type ImprovementNote = {
  metric: string;
  direction: string;
  message: string;
  severity?: string;
};

export type Finding = {
  id: string;
  finding_type: string;
  finding_id?: string | null;
  finding_instance_id?: string | null;
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
  gap_recommendation?: string | null;
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
  status: "pending" | "processing" | "done" | "error" | "needs_review";
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
  created_at?: string | null;
  updated_at?: string | null;
  intake_metadata?: import("@/lib/upload/job-errors").IntakeMetadata | null;
  pipeline_stage?:
    | "pending"
    | "transform"
    | "rules"
    | "evidence_pack"
    | "ai_analyst"
    | "verification"
    | "report_ready"
    | "needs_review"
    | "error"
    | null;
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
