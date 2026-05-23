const FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8000";
const API_KEY = process.env.FASTAPI_API_KEY || "dev-secret";
const DEV_ORG_ID =
  process.env.DEV_ORG_ID || "11111111-1111-1111-1111-111111111111";

export function getFastApiBase(): string {
  return FASTAPI_URL.replace(/\/$/, "");
}

export function getProxyHeaders(orgId?: string): HeadersInit {
  return {
    "X-API-Key": API_KEY,
    "X-Org-Id": orgId || DEV_ORG_ID,
  };
}
