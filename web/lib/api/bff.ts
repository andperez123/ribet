import { auth } from "@clerk/nextjs/server";
import { cookies } from "next/headers";

const FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8000";
const API_KEY = process.env.FASTAPI_API_KEY || "dev-secret";
const DEV_ORG_ID =
  process.env.DEV_ORG_ID || "11111111-1111-1111-1111-111111111111";

const DEMO_COOKIE = "ribet-demo-org";
const CLERK_ENABLED = Boolean(
  process.env.CLERK_SECRET_KEY && process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
);

export function getFastApiBase(): string {
  return FASTAPI_URL.replace(/\/$/, "");
}

async function lookupOrCreateLocalOrg(
  clerkOrgId: string,
  name: string
): Promise<string> {
  const res = await fetch(`${getFastApiBase()}/v1/org/from-clerk`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ clerk_org_id: clerkOrgId, name }),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`org provisioning failed: ${res.status}`);
  }
  const data = (await res.json()) as { org_id: string };
  return data.org_id;
}

export async function resolveOrgId(explicitOrgId?: string): Promise<string> {
  if (explicitOrgId) return explicitOrgId;
  const cookieStore = await cookies();
  const demo = cookieStore.get(DEMO_COOKIE)?.value;
  if (demo) return demo;

  if (CLERK_ENABLED) {
    try {
      const { orgId, orgSlug } = await auth();
      if (orgId) {
        try {
          return await lookupOrCreateLocalOrg(orgId, orgSlug || "Organization");
        } catch (err) {
          console.error(
            "[bff] org provisioning failed, using DEV_ORG_ID:",
            err
          );
        }
      }
    } catch (err) {
      console.error("[bff] Clerk auth failed, using DEV_ORG_ID:", err);
    }
  }

  return DEV_ORG_ID;
}

export async function getProxyHeaders(orgId?: string): Promise<HeadersInit> {
  const resolved = await resolveOrgId(orgId);
  return {
    "X-API-Key": API_KEY,
    "X-Org-Id": resolved,
  };
}

/** Sync headers for routes that cannot use async cookies (use DEV org). */
export function getProxyHeadersSync(orgId?: string): HeadersInit {
  return {
    "X-API-Key": API_KEY,
    "X-Org-Id": orgId || DEV_ORG_ID,
  };
}
