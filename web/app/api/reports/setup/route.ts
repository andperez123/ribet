import { proxyGet, proxyPutJson } from "@/lib/api/proxy";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const preview = searchParams.get("preview");
  const params = new URLSearchParams();
  if (preview === "true") params.set("preview", "true");
  return proxyGet("/v1/reports/setup", params);
}

export async function PUT(request: Request) {
  const body = await request.text();
  return proxyPutJson("/v1/reports/setup", body || "{}");
}
