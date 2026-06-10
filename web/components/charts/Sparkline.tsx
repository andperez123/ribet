"use client";

import { Line, LineChart, ResponsiveContainer } from "recharts";
import { CHART_COLORS } from "./colors";

export function Sparkline({
  data,
  color = CHART_COLORS.green,
  height = 32,
}: {
  data: number[];
  color?: string;
  height?: number;
}) {
  if (!data.length) return null;

  const points = data.map((value, i) => ({ i, value }));

  return (
    <div style={{ height, width: "100%" }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
