import { type NextRequest, NextResponse } from "next/server";

/**
 * Next.js 16+ route proxy (replaces middleware.ts).
 * Currently passes all requests through.
 * Add auth token checks here once the auth layer is implemented.
 */
export function proxy(request: NextRequest) {
  // TODO: uncomment when auth is ready
  // const token = request.cookies.get("token");
  // if (!token && request.nextUrl.pathname.startsWith("/(dashboard)")) {
  //   return NextResponse.redirect(new URL("/login", request.url));
  // }

  return NextResponse.next();
}

/**
 * Scope proxy to real routes only — skip static assets and Next internals.
 */
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|public/).*)" ],
};
