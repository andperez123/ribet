import { NextRequest } from "next/server";
import { proxyGet } from "@/lib/api/proxy";

export async function GET(req: NextRequest) {
  const limit = req.nextUrl.searchParams.get("limit");
  const search = new URLSearchParams();
  if (limit) search.set("limit", limit);
  return proxyGet("/v1/ingest/jobs", search);
}
