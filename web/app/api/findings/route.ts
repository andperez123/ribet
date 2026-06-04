import { NextRequest } from "next/server";
import { proxyGet } from "@/lib/api/proxy";

export async function GET(req: NextRequest) {
  const limit = req.nextUrl.searchParams.get("limit");
  const reportId = req.nextUrl.searchParams.get("report_id");
  const search = new URLSearchParams();
  if (limit) search.set("limit", limit);
  if (reportId) search.set("report_id", reportId);
  return proxyGet("/v1/findings", search);
}
