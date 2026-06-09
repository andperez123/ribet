import { NextRequest } from "next/server";
import { proxyPostJson } from "@/lib/api/proxy";

export async function POST(req: NextRequest) {
  const body = await req.text();
  return proxyPostJson("/v1/chat/query", body);
}
