import { NextRequest } from "next/server";
import { proxyGet } from "@/lib/api/proxy";

export async function GET(req: NextRequest) {
  const reportId = req.nextUrl.searchParams.get("report_id");
  const search = new URLSearchParams();
  if (reportId) search.set("report_id", reportId);
  const qs = search.toString();
  return proxyGet(`/v1/brief/weekly${qs ? `?${qs}` : ""}`);
}
