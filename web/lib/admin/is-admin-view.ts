import { cookies } from "next/headers";

/** Server-only: admin evidence/debug panels and local dev override. */
export async function isAdminView(): Promise<boolean> {
  if (process.env.RIBET_DEBUG === "true") return true;
  if (process.env.NODE_ENV === "development") return true;

  const secret = process.env.ADMIN_SECRET;
  if (!secret) return false;

  const cookieStore = await cookies();
  return cookieStore.get("ribet-admin")?.value === secret;
}
