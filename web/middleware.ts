import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const ADMIN_COOKIE = "ribet-admin";

export function middleware(request: NextRequest) {
  if (!request.nextUrl.pathname.startsWith("/admin")) {
    return NextResponse.next();
  }

  const secret = process.env.ADMIN_SECRET;
  if (!secret) {
    return new NextResponse("Admin not configured", { status: 503 });
  }

  const keyParam = request.nextUrl.searchParams.get("key");
  if (keyParam === secret) {
    const url = request.nextUrl.clone();
    url.searchParams.delete("key");
    const response = NextResponse.redirect(url);
    response.cookies.set(ADMIN_COOKIE, secret, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 7,
    });
    return response;
  }

  const cookie = request.cookies.get(ADMIN_COOKIE)?.value;
  if (cookie === secret) {
    return NextResponse.next();
  }

  return new NextResponse("Unauthorized — append ?key=YOUR_ADMIN_SECRET", {
    status: 401,
  });
}

export const config = {
  matcher: "/admin/:path*",
};
