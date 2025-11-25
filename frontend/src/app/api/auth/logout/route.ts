import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  // Clear authentication cookies
  const response = NextResponse.redirect(`${process.env.AUTH0_BASE_URL}/login`);

  response.cookies.delete('auth_token');
  response.cookies.delete('user_email');

  return response;
}

