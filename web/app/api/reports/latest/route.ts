import { proxyGet } from "@/lib/api/proxy";

export async function GET() {
  return proxyGet("/v1/reports/latest");
}
