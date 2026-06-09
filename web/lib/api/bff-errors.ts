import { NextResponse } from "next/server";
import { OrgResolutionError, getProxyHeaders } from "./bff";

export function bffAuthErrorResponse(err: unknown): NextResponse | null {
  if (err instanceof OrgResolutionError) {
    return NextResponse.json({ detail: err.message }, { status: 401 });
  }
  return null;
}

/** Returns proxy headers or a 401 NextResponse when org resolution fails. */
export async function resolveProxyHeaders(): Promise<HeadersInit | NextResponse> {
  try {
    return await getProxyHeaders();
  } catch (err) {
    const authResp = bffAuthErrorResponse(err);
    if (authResp) return authResp;
    throw err;
  }
}
