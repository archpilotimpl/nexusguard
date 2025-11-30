"""Auth0 middleware for token validation."""
from fastapi import HTTPException, status, Request
from typing import Optional
import jwt
from jose import JWTError
import os


class Auth0Middleware:
    """Middleware for Auth0 JWT token validation."""

    def __init__(self, domain: str, api_audience: str):
        self.domain = domain
        self.api_audience = api_audience
        self.algorithms = ["RS256"]
        self.jwks_client = None

    async def verify_token(self, token: str) -> dict:
        """Verify Auth0 JWT token."""
        try:
            # Decode header to get kid
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token header"
                )

            # Note: In production, implement proper JWKS client
            # to fetch and cache public keys from Auth0

            # For development, you can decode without verification
            # In production, use python-jose with proper key validation
            payload = jwt.decode(
                token,
                options={"verify_signature": False},  # WARNING: Only for development!
            )

            # Verify standard claims
            if payload.get("iss") != f"https://{self.domain}/":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token issuer"
                )

            return payload

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )


async def get_auth0_token(request: Request) -> str:
    """Extract and return Auth0 token from request."""
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        return token
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )


async def verify_auth0_token(request: Request) -> dict:
    """Verify Auth0 token and return payload."""
    token = await get_auth0_token(request)

    domain = os.getenv("AUTH0_DOMAIN")
    api_audience = os.getenv("AUTH0_API_IDENTIFIER")

    middleware = Auth0Middleware(domain, api_audience)
    return await middleware.verify_token(token)

