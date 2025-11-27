import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get('code');
  const state = searchParams.get('state');

  if (!code) {
    return NextResponse.json({ error: 'Missing authorization code' }, { status: 400 });
  }

  try {
    // Exchange authorization code for tokens
    const tokenUrl = `${process.env.AUTH0_ISSUER_BASE_URL}/oauth/token`;
    const tokenResponse = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        client_id: process.env.AUTH0_CLIENT_ID,
        client_secret: process.env.AUTH0_CLIENT_SECRET,
        code,
        grant_type: 'authorization_code',
        redirect_uri: `${process.env.AUTH0_BASE_URL}/api/auth/callback`,
      }),
    });

    if (!tokenResponse.ok) {
      const error = await tokenResponse.json();
      console.error('Token exchange error:', error);
      return NextResponse.json({ error: 'Token exchange failed' }, { status: 400 });
    }

    const tokens = await tokenResponse.json();

    // Get user info from Auth0
    const userInfoUrl = `${process.env.AUTH0_ISSUER_BASE_URL}/userinfo`;
    const userResponse = await fetch(userInfoUrl, {
      headers: {
        'Authorization': `Bearer ${tokens.access_token}`,
      },
    });

    if (!userResponse.ok) {
      console.error('User info error');
      return NextResponse.json({ error: 'Failed to get user info' }, { status: 400 });
    }

    const userInfo = await userResponse.json();

    // Store tokens in httpOnly cookie
    const response = NextResponse.redirect(`${process.env.AUTH0_BASE_URL}/dashboard`);
    response.cookies.set('auth_token', tokens.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: tokens.expires_in,
    });

    // Also store user info (not sensitive)
    response.cookies.set('user_email', userInfo.email, {
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
    });

    return response;
  } catch (error) {
    console.error('Callback error:', error);
    return NextResponse.json({ error: 'Authentication failed' }, { status: 500 });
  }
}

