import { NextResponse } from "next/server";
import { OrgResolutionError } from "./bff";

export function bffAuthErrorResponse(err: unknown): NextResponse | null {
  if (err instanceof OrgResolutionError) {
    return NextResponse.json({ detail: err.message }, { status: 401 });
  }
  return null;
}
