import { NextResponse, type NextRequest } from "next/server";

/**
 * UX-only route guard.
 *
 * Checks for `talign_session` — a non-httpOnly flag cookie set alongside
 * the real (httpOnly) refresh token, see backend app/api/v1/auth.py.
 * This is NOT the security boundary: a visitor could forge this cookie
 * and it would only get them past this redirect, not past the API's
 * `get_current_user` bearer-token check. Its only job is avoiding a
 * flash of protected content / unnecessary round-trip before the real
 * check (AuthProvider's silent refresh) resolves.
 */
export function middleware(request: NextRequest) {
  const hasSessionFlag = request.cookies.has("talign_session");
  const { pathname } = request.nextUrl;

  const isProtectedRoute =
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/jobs") ||
    pathname.startsWith("/applications") ||
    pathname.startsWith("/pipeline") ||
    pathname.startsWith("/knowledge");
  const isAuthRoute =
    pathname.startsWith("/login") || pathname.startsWith("/register");

  if (isProtectedRoute && !hasSessionFlag) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (isAuthRoute && hasSessionFlag) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/jobs/:path*",
    "/applications/:path*",
    "/pipeline/:path*",
    "/knowledge/:path*",
    "/login",
    "/register/:path*",
  ],
};
