import { Card } from "@/components/ui/Card";
import type { HealthHistory } from "@/lib/types/report";

export function HealthTrend({ history }: { history: HealthHistory }) {
  const snapshots = [...history.snapshots].reverse();
  if (!snapshots.length) return null;

  const max = Math.max(...snapshots.map((s) => s.score), 1);

  return (
    <Card>
      <p className="text-sm font-medium text-rivet-text">Health trend</p>
      <div className="mt-6 flex h-24 items-end gap-1.5">
        {snapshots.map((snap, i) => (
          <div
            key={i}
            className="flex flex-1 flex-col items-center gap-1"
            title={`${snap.score} — ${snap.status}`}
          >
            <div
              className="w-full rounded-t bg-rivet-green/70 transition-all"
              style={{ height: `${Math.max(8, (snap.score / max) * 100)}%` }}
            />
          </div>
        ))}
      </div>
      <p className="mt-3 text-xs text-rivet-muted">
        Last {snapshots.length} snapshots (oldest → newest)
      </p>
    </Card>
  );
}
