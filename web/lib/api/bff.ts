import { auth } from "@clerk/nextjs/server";
import { cookies } from "next/headers";

const DEV_API_KEY = "dev-secret";
const FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8000";
const DEV_ORG_ID =
  process.env.DEV_ORG_ID || "11111111-1111-1111-1111-111111111111";

const DEMO_COOKIE = "ribet-demo-org";
const CLERK_ENABLED = Boolean(
  process.env.CLERK_SECRET_KEY && process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
);

export class OrgResolutionError extends Error {
  constructor(message = "Sign in required to access this organization.") {
    super(message);
    this.name = "OrgResolutionError";
  }
}

function isProductionEnv(): boolean {
  return (
    process.env.NODE_ENV === "production" ||
    process.env.RIBET_ENV === "production"
  );
}

export function getBffApiKey(): string {
  const key = (process.env.FASTAPI_API_KEY || "").trim();
  if (isProductionEnv()) {
    if (!key) {
      throw new Error("FASTAPI_API_KEY is required in production");
    }
    if (key === DEV_API_KEY) {
      throw new Error("FASTAPI_API_KEY must not use the dev default in production");
    }
  }
  return key || DEV_API_KEY;
}

export function getFastApiBase(): string {
  return FASTAPI_URL.replace(/\/$/, "");
}

const PERSONAL_ORG_PREFIX = "user_";

function personalClerkOrgId(clerkUserId: string): string {
  return `${PERSONAL_ORG_PREFIX}${clerkUserId}`;
}

async function lookupOrCreateLocalOrg(
  clerkOrgId: string,
  name: string
): Promise<string> {
  const res = await fetch(`${getFastApiBase()}/v1/org/from-clerk`, {
    method: "POST",
    headers: {
      "X-API-Key": getBffApiKey(),
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

  const production = isProductionEnv();
  const cookieStore = await cookies();

  if (CLERK_ENABLED) {
    try {
      const { orgId, orgSlug, userId } = await auth();
      if (orgId) {
        try {
          return await lookupOrCreateLocalOrg(orgId, orgSlug || "Organization");
        } catch (err) {
          console.error("[bff] org provisioning failed:", err);
          if (production) {
            throw new OrgResolutionError(
              "Could not provision your organization. Try again or contact support."
            );
          }
        }
      }
      if (userId) {
        try {
          return await lookupOrCreateLocalOrg(
            personalClerkOrgId(userId),
            "My workspace"
          );
        } catch (err) {
          console.error("[bff] personal workspace provisioning failed:", err);
          if (production) {
            throw new OrgResolutionError(
              "Could not provision your workspace. Try again or contact support."
            );
          }
        }
      }
      if (production) {
        throw new OrgResolutionError();
      }
    } catch (err) {
      if (err instanceof OrgResolutionError) throw err;
      console.error("[bff] Clerk auth failed:", err);
      if (production) {
        throw new OrgResolutionError();
      }
    }
  } else if (production) {
    throw new OrgResolutionError(
      "Authentication is not configured. Set Clerk keys on the web service."
    );
  }

  // Demo cookie only in local/dev — never overrides a signed-in Clerk session.
  const demo = cookieStore.get(DEMO_COOKIE)?.value;
  if (demo) return demo;

  return DEV_ORG_ID;
}

export async function getProxyHeaders(orgId?: string): Promise<HeadersInit> {
  const resolved = await resolveOrgId(orgId);
  return {
    "X-API-Key": getBffApiKey(),
    "X-Org-Id": resolved,
  };
}

/** Sync headers for routes that cannot use async cookies (use DEV org). */
export function getProxyHeadersSync(orgId?: string): HeadersInit {
  return {
    "X-API-Key": getBffApiKey(),
    "X-Org-Id": orgId || DEV_ORG_ID,
  };
}
