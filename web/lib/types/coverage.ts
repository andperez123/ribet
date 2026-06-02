export type CoverageItem = {
  key: string;
  label: string;
  sector: string;
  covered: boolean;
  uploadable: boolean;
};

export type ConfidenceBreakdownItem = {
  key: string;
  label: string;
  weight: number;
  covered: boolean;
};

export type NextUpload = {
  key: string;
  label: string;
  confidence_if_uploaded: number;
};

export type DataGap = {
  id: string;
  gap_type: string;
  reason: string;
  recommended_uploads: string[];
  requested_report_types: string[];
  requested_sector: string | null;
  confidence_if_uploaded: number | null;
  priority: string;
  status: string;
};

export type OrgCoverage = {
  understood: CoverageItem[];
  needed: CoverageItem[];
  analysis_confidence: number;
  confidence_breakdown: ConfidenceBreakdownItem[];
  next_upload: NextUpload | null;
  gaps: DataGap[];
};
