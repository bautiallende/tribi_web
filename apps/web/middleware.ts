import {NextRequest, NextResponse} from 'next/server';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();
  
  // Check if locale cookie exists, if not set default
  if (!request.cookies.has('NEXT_LOCALE')) {
    response.cookies.set('NEXT_LOCALE', 'en', {
      maxAge: 365 * 24 * 60 * 60, // 1 year
      path: '/',
    });
  }
  
  return response;
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
