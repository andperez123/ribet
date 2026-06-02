import { NextResponse } from "next/server";
import { API } from "@/lib/api/endpoints";
import { proxyGet } from "@/lib/api/proxy";

export async function GET() {
  return proxyGet(API.org.coverage);
}
