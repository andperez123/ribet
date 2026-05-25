import { NextResponse } from "next/server";
import { getFastApiBase } from "@/lib/api/bff";

const DEMO_COOKIE = "ribet-demo-org";

export async function POST() {
  const res = await fetch(`${getFastApiBase()}/v1/org/demo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  const body = await res.text();
  if (!res.ok) {
    return new NextResponse(body, { status: res.status });
  }

  const data = JSON.parse(body) as { org_id: string };
  const response = NextResponse.json(JSON.parse(body));
  response.cookies.set(DEMO_COOKIE, data.org_id, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24,
  });
  return response;
}
