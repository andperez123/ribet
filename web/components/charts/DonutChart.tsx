"use client";

import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { CHART_COLORS } from "./colors";

export type DonutSlice = {
  name: string;
  value: number;
  color?: string;
};

function DonutTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; payload: DonutSlice }>;
}) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  return (
    <div className="rounded-lg border border-ribet-border bg-ribet-card px-3 py-2 text-xs shadow-soft">
      <p className="font-medium text-ribet-text">{item.name}</p>
      <p className="tabular-nums text-ribet-muted">
        {item.value.toLocaleString()}
      </p>
    </div>
  );
}

export function DonutChart({
  data,
  height = 180,
  centerLabel,
  centerValue,
}: {
  data: DonutSlice[];
  height?: number;
  centerLabel?: string;
  centerValue?: string;
}) {
  const filtered = data.filter((d) => d.value > 0);
  if (!filtered.length) return null;

  const defaultColors = [
    CHART_COLORS.green,
    CHART_COLORS.amber,
    CHART_COLORS.orange,
    CHART_COLORS.risk,
    CHART_COLORS.muted,
  ];

  return (
    <div className="relative" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={filtered}
            cx="50%"
            cy="50%"
            innerRadius="58%"
            outerRadius="82%"
            dataKey="value"
            stroke="none"
            isAnimationActive
            animationDuration={700}
          >
            {filtered.map((entry, i) => (
              <Cell
                key={entry.name}
                fill={entry.color ?? defaultColors[i % defaultColors.length]}
              />
            ))}
          </Pie>
          <Tooltip content={<DonutTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      {(centerLabel || centerValue) && (
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
          {centerValue && (
            <span className="text-lg font-semibold tabular-nums text-ribet-text">
              {centerValue}
            </span>
          )}
          {centerLabel && (
            <span className="text-[10px] text-ribet-muted">{centerLabel}</span>
          )}
        </div>
      )}
    </div>
  );
}
