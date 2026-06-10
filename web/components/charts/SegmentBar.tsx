"use client";

import { CHART_COLORS } from "./colors";

export type SegmentItem = {
  key: string;
  label: string;
  weight: number;
  covered: boolean;
  highlighted?: boolean;
};

export function SegmentBar({
  segments,
  showLabels = true,
}: {
  segments: SegmentItem[];
  showLabels?: boolean;
}) {
  const total = segments.reduce((sum, s) => sum + s.weight, 0) || 1;

  return (
    <div className="space-y-3">
      <div className="flex h-3 overflow-hidden rounded-full bg-ribet-border/50">
        {segments.map((seg) => (
          <div
            key={seg.key}
            className={`h-full transition-all ${
              seg.highlighted ? "ring-2 ring-ribet-green ring-offset-1" : ""
            }`}
            style={{
              width: `${(seg.weight / total) * 100}%`,
              backgroundColor: seg.covered
                ? CHART_COLORS.green
                : seg.highlighted
                  ? CHART_COLORS.amber
                  : CHART_COLORS.border,
              opacity: seg.covered ? 1 : seg.highlighted ? 0.85 : 0.6,
            }}
            title={`${seg.label}: ${seg.weight}%`}
          />
        ))}
      </div>
      {showLabels && (
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {segments.map((seg) => (
            <div key={seg.key} className="flex items-center gap-1.5 text-xs">
              <span
                className="h-2 w-2 rounded-full"
                style={{
                  backgroundColor: seg.covered
                    ? CHART_COLORS.green
                    : CHART_COLORS.border,
                }}
              />
              <span
                className={
                  seg.highlighted
                    ? "font-medium text-ribet-text"
                    : "text-ribet-muted"
                }
              >
                {seg.label}
                {seg.highlighted && !seg.covered && " → next"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
