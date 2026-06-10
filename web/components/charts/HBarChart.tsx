"use client";

import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatCurrency } from "@/lib/dashboard/utils";
import { CHART_COLORS } from "./colors";

export type HBarItem = {
  label: string;
  value: number;
  color?: string;
  risk?: boolean;
};

function BarTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: HBarItem }>;
}) {
  if (!active || !payload?.length) return null;
  const item = payload[0].payload;
  return (
    <div className="rounded-lg border border-ribet-border bg-ribet-card px-3 py-2 text-xs shadow-soft">
      <p className="font-medium text-ribet-text">{item.label}</p>
      <p className="tabular-nums text-ribet-muted">{formatCurrency(item.value)}</p>
    </div>
  );
}

export function HBarChart({
  data,
  height,
}: {
  data: HBarItem[];
  height?: number;
}) {
  const filtered = data.filter((d) => d.value > 0);
  if (!filtered.length) return null;

  const barHeight = 28;
  const computedHeight = height ?? Math.max(120, filtered.length * barHeight + 16);

  return (
    <div style={{ height: computedHeight }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={filtered}
          layout="vertical"
          margin={{ top: 0, right: 8, left: 0, bottom: 0 }}
        >
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="label"
            width={110}
            tick={{ fontSize: 11, fill: CHART_COLORS.muted }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<BarTooltip />} cursor={{ fill: "transparent" }} />
          <Bar
            dataKey="value"
            radius={[0, 6, 6, 0]}
            barSize={16}
            isAnimationActive
            animationDuration={700}
          >
            {filtered.map((entry, i) => (
              <Cell
                key={entry.label}
                fill={
                  entry.color ??
                  (entry.risk ? CHART_COLORS.risk : CHART_COLORS.green)
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
