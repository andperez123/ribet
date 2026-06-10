export const CHART_COLORS = {
  green: "#A3C957",
  greenMuted: "#A3C95799",
  risk: "#D96B6B",
  amber: "#D4A24C",
  orange: "#E07B4A",
  muted: "#6B6B66",
  border: "#E8E8E3",
  card: "#FFFFFF",
  ink: "#111111",
  inkSoft: "#2A2A26",
} as const;

export const AGING_COLORS = [
  CHART_COLORS.green,
  "#8BB84A",
  CHART_COLORS.amber,
  CHART_COLORS.orange,
  CHART_COLORS.risk,
] as const;

export const SEVERITY_BAR_COLORS = [
  CHART_COLORS.green,
  CHART_COLORS.amber,
  CHART_COLORS.orange,
  CHART_COLORS.risk,
] as const;

export function scoreColor(score: number): string {
  if (score >= 75) return CHART_COLORS.green;
  if (score >= 55) return CHART_COLORS.amber;
  if (score >= 40) return CHART_COLORS.orange;
  return CHART_COLORS.risk;
}
