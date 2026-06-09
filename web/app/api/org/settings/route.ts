import { NextRequest, NextResponse } from "next/server";
import { getFastApiBase } from "@/lib/api/bff";
import { resolveProxyHeaders } from "@/lib/api/bff-errors";

export async function GET() {
  const headers = await resolveProxyHeaders();
  if (headers instanceof NextResponse) return headers;

  const res = await fetch(`${getFastApiBase()}/v1/org/settings`, {
    headers,
    cache: "no-store",
  });
  const body = await res.text();
  return new NextResponse(body, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}

export async function PATCH(req: NextRequest) {
  const headers = await resolveProxyHeaders();
  if (headers instanceof NextResponse) return headers;

  const body = await req.text();
  const res = await fetch(`${getFastApiBase()}/v1/org/settings`, {
    method: "PATCH",
    headers: {
      ...headers,
      "Content-Type": "application/json",
    },
    body,
  });
  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
