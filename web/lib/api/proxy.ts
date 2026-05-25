import { NextResponse } from "next/server";
import { getFastApiBase, getProxyHeaders } from "./bff";

export async function proxyGet(path: string, search?: URLSearchParams) {
  const qs = search?.toString();
  const url = `${getFastApiBase()}${path}${qs ? `?${qs}` : ""}`;
  const res = await fetch(url, {
    headers: await getProxyHeaders(),
    cache: "no-store",
  });
  const body = await res.text();
  return new NextResponse(body, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
