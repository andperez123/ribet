import { proxyPostJson } from "@/lib/api/proxy";

export async function POST(request: Request) {
  const body = await request.text();
  return proxyPostJson("/v1/reports/regenerate", body || "{}");
}
