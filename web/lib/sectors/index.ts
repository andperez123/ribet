export {
  SECTORS,
  DEFAULT_SECTOR,
  type SectorId,
  type SectorDef,
} from "./capabilities";

export type SectorStatus = {
  id: string;
  label: string;
  covered: boolean;
  count: number;
  last_upload_at: string | null;
  last_report_type: string | null;
};

export type CapabilityStatus = {
  id: string;
  name: string;
  description: string;
  unlocked: boolean;
  requirement: string | null;
};

export type OrgProgress = {
  sectors: SectorStatus[];
  capabilities: CapabilityStatus[];
  coverage_count: number;
};
