import { NextRequest, NextResponse } from "next/server";
import { getFastApiBase, getProxyHeaders } from "@/lib/api/bff";

export async function GET() {
  const res = await fetch(`${getFastApiBase()}/v1/org/settings`, {
    headers: await getProxyHeaders(),
    cache: "no-store",
  });
  const body = await res.text();
  return new NextResponse(body, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}

export async function PATCH(req: NextRequest) {
  const body = await req.text();
  const res = await fetch(`${getFastApiBase()}/v1/org/settings`, {
    method: "PATCH",
    headers: {
      ...(await getProxyHeaders()),
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
