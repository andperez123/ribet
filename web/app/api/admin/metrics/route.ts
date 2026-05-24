import { NextResponse } from "next/server";
import { getFastApiBase } from "@/lib/api/bff";

export async function GET() {
  const adminKey = process.env.ADMIN_API_KEY;
  if (!adminKey) {
    return NextResponse.json({ error: "Admin API not configured" }, { status: 503 });
  }

  const res = await fetch(`${getFastApiBase()}/v1/admin/metrics`, {
    headers: { "X-Admin-Key": adminKey },
    cache: "no-store",
  });

  const body = await res.text();
  return new NextResponse(body, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
