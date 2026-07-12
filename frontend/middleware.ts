import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const isLoginPage = request.nextUrl.pathname.startsWith('/login');
  const hasDemoAuth = request.cookies.has('demo_auth');

  // If they don't have the demo_auth cookie and aren't on the login page, redirect them.
  if (!hasDemoAuth && !isLoginPage) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // If they DO have the cookie and try to visit the login page, redirect to dashboard.
  if (hasDemoAuth && isLoginPage) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next();
}

// See "Matching Paths" below to learn more
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
