import { NextRequest, NextResponse } from "next/server";
import { getFastApiBase } from "@/lib/api/bff";
import { resolveProxyHeaders } from "@/lib/api/bff-errors";

type Params = { params: Promise<{ id: string }> };

export async function GET(_req: NextRequest, { params }: Params) {
  const { id } = await params;
  const headers = await resolveProxyHeaders();
  if (headers instanceof NextResponse) return headers;

  const res = await fetch(`${getFastApiBase()}/v1/reports/${id}/pdf`, {
    headers,
  });

  if (!res.ok) {
    const text = await res.text();
    return new NextResponse(text, { status: res.status });
  }

  const blob = await res.arrayBuffer();
  return new NextResponse(blob, {
    status: 200,
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `attachment; filename="ribet-report-${id}.pdf"`,
    },
  });
}
