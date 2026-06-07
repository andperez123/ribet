import { NextResponse } from "next/server";
import { bffAuthErrorResponse } from "./bff-errors";
import { getFastApiBase, getProxyHeaders } from "./bff";

export async function proxyDelete(path: string) {
  const url = `${getFastApiBase()}${path}`;
  let headers: HeadersInit;
  try {
    headers = await getProxyHeaders();
  } catch (err) {
    const authResp = bffAuthErrorResponse(err);
    if (authResp) return authResp;
    throw err;
  }
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
  let headers: HeadersInit;
  try {
    headers = await getProxyHeaders();
  } catch (err) {
    const authResp = bffAuthErrorResponse(err);
    if (authResp) return authResp;
    throw err;
  }
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
