import type { MetricKey } from "@/lib/dashboard/insight-metrics";
import type { AnalystOutput } from "@/lib/types/report";

export function metricTakeawaysMap(
  analystOutput?: AnalystOutput | null
): Partial<Record<MetricKey, string>> {
  const map: Partial<Record<MetricKey, string>> = {};
  for (const item of analystOutput?.metric_takeaways ?? []) {
    if (item.metric_key && item.takeaway) {
      map[item.metric_key as MetricKey] = item.takeaway;
    }
  }
  return map;
}
