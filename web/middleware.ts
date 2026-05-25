import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const ADMIN_COOKIE = "ribet-admin";

const isProtectedRoute = createRouteMatcher(["/dashboard(.*)"]);
const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/legal(.*)",
  "/api(.*)",
]);

function adminGuard(request: NextRequest): NextResponse | null {
  if (!request.nextUrl.pathname.startsWith("/admin")) {
    return null;
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

const clerkEnabled = Boolean(
  process.env.CLERK_SECRET_KEY && process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
);

export default clerkEnabled
  ? clerkMiddleware(async (auth, request) => {
      const admin = adminGuard(request);
      if (admin) return admin;

      if (isPublicRoute(request)) {
        return;
      }
      if (isProtectedRoute(request)) {
        await auth.protect();
      }
    })
  : function middleware(request: NextRequest) {
      const admin = adminGuard(request);
      return admin ?? NextResponse.next();
    };

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
