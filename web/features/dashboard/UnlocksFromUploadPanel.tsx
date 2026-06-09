import { Card } from "@/components/ui/Card";
import type { ReportContract, ReportUnlock, UnlocksFromUpload } from "@/lib/types/report";

function normalizeUnlocks(
  unlocks?: ReportContract["unlocks_from_this_upload"]
): UnlocksFromUpload | null {
  if (!unlocks) return null;
  if (Array.isArray(unlocks)) {
    return { unlocked: unlocks, still_gated: [] };
  }
  return unlocks;
}

export function UnlocksFromUploadPanel({
  unlocks,
}: {
  unlocks?: ReportContract["unlocks_from_this_upload"];
}) {
  const split = normalizeUnlocks(unlocks);
  if (!split?.unlocked.length && !split?.still_gated.length) return null;

  return (
    <Card className="space-y-4">
      <h2 className="text-sm font-semibold text-ribet-text">Unlocks from this upload</h2>
      <div className="grid gap-4 md:grid-cols-2">
        <UnlockColumn title="Newly unlocked" items={split?.unlocked ?? []} positive />
        <UnlockColumn title="Still gated" items={split?.still_gated ?? []} />
      </div>
    </Card>
  );
}

function UnlockColumn({
  title,
  items,
  positive,
}: {
  title: string;
  items: ReportUnlock[];
  positive?: boolean;
}) {
  if (!items.length) {
    return (
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
          {title}
        </p>
        <p className="mt-2 text-sm text-ribet-muted">None</p>
      </div>
    );
  }

  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-ribet-muted">
        {title}
      </p>
      <ul className="mt-2 space-y-2">
        {items.map((unlock) => (
          <li
            key={`${unlock.type}-${unlock.message}`}
            className="flex gap-2 text-sm text-ribet-text"
          >
            <span className={positive ? "text-ribet-green" : "text-ribet-muted"} aria-hidden>
              {positive ? "✓" : "○"}
            </span>
            {unlock.message}
          </li>
        ))}
      </ul>
    </div>
  );
}
