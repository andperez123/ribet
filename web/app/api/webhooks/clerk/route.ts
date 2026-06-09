import { NextRequest, NextResponse } from "next/server";
import { Webhook } from "svix";
import { getBffApiKey, getFastApiBase } from "@/lib/api/bff";

type ClerkOrgEvent = {
  type: string;
  data: {
    id: string;
    name?: string;
    slug?: string;
  };
};

export async function POST(req: NextRequest) {
  const secret = process.env.CLERK_WEBHOOK_SECRET;
  if (!secret) {
    return NextResponse.json({ error: "Webhook not configured" }, { status: 503 });
  }

  const payload = await req.text();
  const headers = {
    "svix-id": req.headers.get("svix-id") ?? "",
    "svix-timestamp": req.headers.get("svix-timestamp") ?? "",
    "svix-signature": req.headers.get("svix-signature") ?? "",
  };

  let event: ClerkOrgEvent;
  try {
    const wh = new Webhook(secret);
    event = wh.verify(payload, headers) as ClerkOrgEvent;
  } catch {
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  if (event.type !== "organization.created") {
    return NextResponse.json({ ok: true, skipped: true });
  }

  const name = event.data.name || event.data.slug || "Organization";
  const res = await fetch(`${getFastApiBase()}/v1/org/from-clerk`, {
    method: "POST",
    headers: {
      "X-API-Key": getBffApiKey(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      clerk_org_id: event.data.id,
      name,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: text }, { status: 502 });
  }

  return NextResponse.json({ ok: true });
}
