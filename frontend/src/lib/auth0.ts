/**
 * Auth0 utility functions for frontend integration
 */

/**
 * Get the authorization token from cookies
 */
export function getAuthToken(): string | null {
  if (typeof document === 'undefined') return null;

  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'auth_token') {
      return decodeURIComponent(value);
    }
  }
  return null;
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return getAuthToken() !== null;
}

/**
 * Get user email from cookies
 */
export function getUserEmail(): string | null {
  if (typeof document === 'undefined') return null;

  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'user_email') {
      return decodeURIComponent(value);
    }
  }
  return null;
}

/**
 * Decode JWT token (without verification - client-side only)
 */
export function decodeToken(token: string) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const payload = JSON.parse(atob(parts[1]));
    return payload;
  } catch (e) {
    console.error('Failed to decode token:', e);
    return null;
  }
}

/**
 * Get Auth0 token expiration time
 */
export function getTokenExpiration(token: string): Date | null {
  const payload = decodeToken(token);
  if (!payload || !payload.exp) return null;

  return new Date(payload.exp * 1000);
}

/**
 * Check if token is expired
 */
export function isTokenExpired(token: string): boolean {
  const expiration = getTokenExpiration(token);
  if (!expiration) return true;

  return new Date() > expiration;
}

/**
 * Make authenticated API request
 */
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getAuthToken();

  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`,
  };

  return fetch(url, {
    ...options,
    headers,
  });
}

/**
 * Logout user
 */
export function logout(): void {
  // For Auth0: redirect to logout endpoint which clears cookies
  // For traditional: store's logout function will handle it
  window.location.href = '/api/auth/logout';
}

