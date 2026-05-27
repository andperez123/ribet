import { NextResponse } from "next/server";

/** Runtime config for the browser (avoids baking NEXT_PUBLIC_* only at Docker build). */
export async function GET() {
  const uploadMode =
    process.env.NEXT_PUBLIC_UPLOAD_MODE === "mock" ? "mock" : "api";

  return NextResponse.json({
    uploadMode,
    clerkEnabled: Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY),
  });
}
