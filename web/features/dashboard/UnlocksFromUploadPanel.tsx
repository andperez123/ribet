import { Card } from "@/components/ui/Card";
import type { ReportUnlock } from "@/lib/types/report";

export function UnlocksFromUploadPanel({
  unlocks,
}: {
  unlocks?: ReportUnlock[];
}) {
  if (!unlocks?.length) return null;

  return (
    <Card className="border-ribet-green/30">
      <h2 className="text-sm font-semibold text-ribet-text">
        New insights unlocked by this upload
      </h2>
      <ul className="mt-3 space-y-2">
        {unlocks.map((unlock) => (
          <li
            key={`${unlock.type}-${unlock.message}`}
            className="flex gap-2 text-sm text-ribet-text"
          >
            <span className="text-ribet-green" aria-hidden>
              ✓
            </span>
            {unlock.message}
          </li>
        ))}
      </ul>
    </Card>
  );
}
