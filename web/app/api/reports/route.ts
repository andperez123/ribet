import { proxyGet } from "@/lib/api/proxy";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  return proxyGet("/v1/reports", searchParams);
}
