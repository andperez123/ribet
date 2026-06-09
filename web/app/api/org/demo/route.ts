import { NextResponse } from "next/server";
import { getFastApiBase } from "@/lib/api/bff";

const DEMO_COOKIE = "ribet-demo-org";

function isProductionEnv(): boolean {
  return (
    process.env.NODE_ENV === "production" ||
    process.env.RIBET_ENV === "production"
  );
}

export async function POST() {
  if (isProductionEnv()) {
    return NextResponse.json(
      { detail: "Demo org creation is disabled in production" },
      { status: 403 }
    );
  }

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
    secure: process.env.NODE_ENV === "production",
  });
  return response;
}
