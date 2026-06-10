"use client";

import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS } from "./colors";

export type TrendPoint = {
  label: string;
  value: number;
  status?: string;
};

function TrendTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: TrendPoint }>;
}) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="rounded-lg border border-ribet-border bg-ribet-card px-3 py-2 text-xs shadow-soft">
      <p className="font-medium text-ribet-text">{point.value}</p>
      {point.status && (
        <p className="text-ribet-muted">{point.status}</p>
      )}
    </div>
  );
}

export function AreaTrend({
  data,
  height = 120,
}: {
  data: TrendPoint[];
  height?: number;
}) {
  if (!data.length) return null;

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="healthGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_COLORS.green} stopOpacity={0.35} />
              <stop offset="100%" stopColor={CHART_COLORS.green} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <XAxis dataKey="label" hide />
          <YAxis domain={[0, 100]} hide />
          <Tooltip content={<TrendTooltip />} />
          <Area
            type="monotone"
            dataKey="value"
            stroke={CHART_COLORS.green}
            strokeWidth={2}
            fill="url(#healthGradient)"
            isAnimationActive
            animationDuration={800}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
