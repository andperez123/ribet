export type OperationalSnapshotOut = {
  period: string;
  health_score: number;
  health_status: string;
  ar_over_90_pct: number | null;
  ar_total: number | null;
  ap_total: number | null;
  inventory_value: number | null;
  vendor_concentration: number | null;
  computed_at: string;
};

export type SnapshotHistoryOut = {
  snapshots: OperationalSnapshotOut[];
};
