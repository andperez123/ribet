import { proxyPostJson } from "@/lib/api/proxy";

export async function POST() {
  return proxyPostJson("/v1/reports/regenerate", "{}");
}
