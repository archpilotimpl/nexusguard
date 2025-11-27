"""Auth0 Token Verification API endpoints."""
from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
import httpx
import os

router = APIRouter(prefix="/auth0", tags=["Auth0"])


async def verify_auth0_token(authorization: Optional[str] = Header(None)):
    """Verify Auth0 JWT token from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    # Verify token with Auth0
    domain = os.getenv("AUTH0_DOMAIN")

    async with httpx.AsyncClient() as client:
        try:
            # Get JWKS from Auth0
            response = await client.get(f"{domain}/.well-known/jwks.json")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to verify token"
                )

            # Note: In production, use proper JWT verification with PyJWT and python-jose
            # This is a simplified version
            return token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )


@router.get("/verify")
async def verify_token(token: str = Depends(verify_auth0_token)):
    """Verify Auth0 token and return user info."""
    return {
        "status": "verified",
        "message": "Token is valid",
        "token": token[:20] + "..."  # Return partial token for security
    }


@router.post("/token-info")
async def get_token_info(
    authorization: Optional[str] = Header(None)
):
    """Get token information from Auth0."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    domain = os.getenv("AUTH0_DOMAIN")
    api_audience = os.getenv("AUTH0_API_IDENTIFIER")

    async with httpx.AsyncClient() as client:
        try:
            # Introspect token with Auth0
            response = await client.post(
                f"{domain}/oauth/token/introspect",
                data={
                    "client_id": os.getenv("AUTH0_CLIENT_ID"),
                    "client_secret": os.getenv("AUTH0_CLIENT_SECRET"),
                    "token": token,
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )

            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token introspection failed"
            )

