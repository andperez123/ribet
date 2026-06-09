import { NextRequest, NextResponse } from "next/server";
import { getFastApiBase } from "@/lib/api/bff";
import { resolveProxyHeaders } from "@/lib/api/bff-errors";

type Params = { params: Promise<{ id: string }> };

export async function GET(_req: NextRequest, { params }: Params) {
  const { id } = await params;
  const headers = await resolveProxyHeaders();
  if (headers instanceof NextResponse) return headers;

  const res = await fetch(`${getFastApiBase()}/v1/ingest/jobs/${id}/mapping`, {
    headers,
    cache: "no-store",
  });

  const body = await res.text();
  return new NextResponse(body, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
