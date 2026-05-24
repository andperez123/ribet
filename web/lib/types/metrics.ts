export type TotalsBlock = {
  orgs: number;
  uploads: number;
  reports: number;
  findings: number;
  active_orgs_30d: number;
};

export type ActivationBlock = {
  rate_pct: number;
  orgs_with_report: number;
  median_time_to_first_report_hours: number | null;
};

export type EngagementBlock = {
  upload_success_rate_pct: number;
  report_yield_rate_pct: number;
  avg_sectors_per_active_org: number;
  repeat_upload_rate_pct: number;
  avg_findings_per_report: number;
};

export type WeeklyBucket = {
  week_start: string;
  uploads: number;
  reports: number;
  new_orgs: number;
  cumulative_reports: number;
};

export type OrgMetricsRow = {
  org_id: string;
  name: string;
  created_at: string;
  uploads: number;
  reports: number;
  sectors_covered: number;
  findings: number;
  last_upload_at: string | null;
  last_report_at: string | null;
  health_score: number | null;
};

export type AdminMetrics = {
  generated_at: string;
  totals: TotalsBlock;
  activation: ActivationBlock;
  engagement: EngagementBlock;
  weekly: WeeklyBucket[];
  orgs: OrgMetricsRow[];
};
