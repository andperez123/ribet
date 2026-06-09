import { NextResponse } from "next/server";
import { resolveProxyHeaders } from "./bff-errors";
import { getFastApiBase } from "./bff";

function isProxyAuthFailure(
  headers: HeadersInit | NextResponse
): headers is NextResponse {
  return headers instanceof NextResponse;
}

export async function proxyDelete(path: string) {
  const url = `${getFastApiBase()}${path}`;
  const headers = await resolveProxyHeaders();
  if (isProxyAuthFailure(headers)) return headers;
  const res = await fetch(url, {
    method: "DELETE",
    headers,
    cache: "no-store",
  });
  const body = await res.text();
  return new NextResponse(body || "{}", {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}

export async function proxyGet(path: string, search?: URLSearchParams) {
  const qs = search?.toString();
  const url = `${getFastApiBase()}${path}${qs ? `?${qs}` : ""}`;
  const headers = await resolveProxyHeaders();
  if (isProxyAuthFailure(headers)) return headers;
  const res = await fetch(url, {
    headers,
    cache: "no-store",
  });
  const body = await res.text();
  return new NextResponse(body, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}

export async function proxyPostJson(path: string, body: string) {
  const url = `${getFastApiBase()}${path}`;
  const headers = await resolveProxyHeaders();
  if (isProxyAuthFailure(headers)) return headers;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      ...Object.fromEntries(new Headers(headers).entries()),
      "Content-Type": "application/json",
    },
    body,
    cache: "no-store",
  });
  const text = await res.text();
  return new NextResponse(text || "{}", {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
