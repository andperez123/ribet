import { NextResponse } from "next/server";
import { getFastApiBase } from "@/lib/api/bff";

export async function GET() {
  try {
    const res = await fetch(`${getFastApiBase()}/health/worker`, {
      cache: "no-store",
    });
    const body = await res.json();
    return NextResponse.json(body, { status: res.status });
  } catch (e) {
    return NextResponse.json(
      {
        ok: false,
        error: e instanceof Error ? e.message : "Worker health check failed",
      },
      { status: 503 }
    );
  }
}
