"use client";

import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import { CHART_COLORS, scoreColor } from "./colors";

export function RadialGauge({
  value,
  max = 100,
  size = 140,
  label,
  sublabel,
  invert = false,
  tone = "light",
}: {
  value: number;
  max?: number;
  size?: number;
  label?: string;
  sublabel?: string;
  invert?: boolean;
  /** "dark" renders light text for use on dark/hero backgrounds. */
  tone?: "light" | "dark";
}) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const display = invert ? max - value : value;
  const color = scoreColor(invert ? 100 - pct : pct);
  const trackColor = tone === "dark" ? "rgba(255,255,255,0.16)" : CHART_COLORS.border;
  const valueClass = tone === "dark" ? "text-white" : "text-ribet-text";
  const labelClass = tone === "dark" ? "text-white/70" : "text-ribet-muted";
  const sublabelClass = tone === "dark" ? "text-white/55" : "text-ribet-muted";
  const data = [
    { value: pct, fill: color },
    { value: 100 - pct, fill: trackColor },
  ];

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            startAngle={90}
            endAngle={-270}
            innerRadius="72%"
            outerRadius="100%"
            dataKey="value"
            stroke="none"
            isAnimationActive
            animationDuration={800}
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className={`text-3xl font-semibold tabular-nums ${valueClass}`}>
          {Math.round(display)}
        </span>
        {label && (
          <span className={`mt-0.5 text-[10px] font-medium uppercase tracking-wide ${labelClass}`}>
            {label}
          </span>
        )}
        {sublabel && (
          <span className={`text-[10px] ${sublabelClass}`}>{sublabel}</span>
        )}
      </div>
    </div>
  );
}
