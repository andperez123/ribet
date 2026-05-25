import { proxyGet } from "@/lib/api/proxy";

export async function GET() {
  return proxyGet("/v1/snapshots/latest");
}
