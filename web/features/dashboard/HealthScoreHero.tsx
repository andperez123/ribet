import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { healthStatusColor } from "@/lib/dashboard/utils";
import type { HealthScore } from "@/lib/types/report";

export function HealthScoreHero({ score }: { score: HealthScore }) {
  const statusClass = healthStatusColor(score.status);

  return (
    <Card className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <p className="text-sm text-rivet-muted">Operational health</p>
        <div className="mt-2 flex items-baseline gap-3">
          <span className="text-5xl font-semibold tracking-tight text-rivet-text">
            {score.score}
          </span>
          <span className="text-lg text-rivet-muted">/ 100</span>
        </div>
        {score.computed_at && (
          <p className="mt-2 text-xs text-rivet-muted">
            Updated {new Date(score.computed_at).toLocaleString()}
          </p>
        )}
      </div>
      <Badge
        variant={
          score.status.toLowerCase().includes("risk") ||
          score.status.toLowerCase().includes("critical")
            ? "risk"
            : "success"
        }
        className={`text-sm ${statusClass}`}
      >
        {score.status}
      </Badge>
    </Card>
  );
}
