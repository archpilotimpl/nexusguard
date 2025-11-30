"""Security utilities for authentication and authorization."""
from datetime import datetime, timedelta
from typing import Optional, Any
import logging
import httpx
from functools import lru_cache
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.primitives import serialization

from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer scheme
security = HTTPBearer()

# Check if Auth0 is enabled
USE_AUTH0 = settings.ENABLE_AUTH0 and settings.AUTH0_DOMAIN and settings.AUTH0_API_IDENTIFIER


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


# ============================================================================
# Auth0 Token Validation
# ============================================================================

@lru_cache(maxsize=1)
def get_auth0_public_keys() -> dict:
    """Fetch and cache Auth0 public keys for token verification."""
    if not USE_AUTH0:
        return {}

    try:
        jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        response = httpx.get(jwks_url, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch Auth0 public keys"
        )


def get_auth0_signing_key(token: str) -> Optional[dict]:
    """Extract the signing key from Auth0 JWKS."""
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token header"
            )

        jwks = get_auth0_public_keys()
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not find signing key"
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token format: {str(e)}"
        )


def decode_auth0_token(token: str) -> dict:
    """Decode and validate an Auth0 JWT token."""
    # If skip verification is enabled, return unverified claims (useful for local/dev)
    logger.info(f"Decoding Auth0 token... Skip verification: {settings.AUTH0_SKIP_VERIFICATION}")

    if settings.AUTH0_SKIP_VERIFICATION:
        logger.warning("AUTH0_SKIP_VERIFICATION is enabled - returning unverified token claims (INSECURE)")
        try:
            # jose has get_unverified_claims
            claims = jwt.get_unverified_claims(token)
            return claims
        except Exception as e:
            logger.error(f"Failed to extract unverified claims: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not parse token"
            )

    import base64
    from cryptography.hazmat.primitives.asymmetric import rsa as crypto_rsa

    def _base64url_to_bytes(val: str) -> bytes:
        # Add padding if necessary
        val = val.encode('utf-8') if isinstance(val, str) else val
        rem = len(val) % 4
        if rem:
            val += b'=' * (4 - rem)
        return base64.urlsafe_b64decode(val)

    try:
        logger.debug("🔍 Validating Auth0 token signature...")
        signing_key = get_auth0_signing_key(token)

        # Prefer JWK 'n'/'e' parameters if present (RSA public key in JWK format)
        if signing_key and signing_key.get("kty") == "RSA" and "n" in signing_key and "e" in signing_key:
            jwk_key = {
                "kty": signing_key.get("kty"),
                "n": signing_key.get("n"),
                "e": signing_key.get("e")
            }
            logger.debug("Using JWK 'n'/'e' parameters for token verification")
            # First try letting python-jose handle the JWK dict directly
            try:
                payload = jwt.decode(
                    token,
                    jwk_key,
                    algorithms=["RS256"],
                    audience=settings.AUTH0_API_IDENTIFIER,
                    issuer=f"https://{settings.AUTH0_DOMAIN}/"
                )
                logger.debug("✓ Auth0 token signature verified successfully using JWK dict")
                logger.debug("✓ Token audience and issuer validated")
                return payload
            except JWTError as e:
                logger.warning(f"JWK (n/e) direct verification failed: {e}; attempting to construct RSA key from n/e")
                # Attempt to build RSA public key from n/e and verify using PEM
                try:
                    n_b = _base64url_to_bytes(signing_key.get('n'))
                    e_b = _base64url_to_bytes(signing_key.get('e'))
                    n_int = int.from_bytes(n_b, 'big')
                    e_int = int.from_bytes(e_b, 'big')

                    public_numbers = crypto_rsa.RSAPublicNumbers(e_int, n_int)
                    public_key = public_numbers.public_key(default_backend())
                    public_pem = public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ).decode('utf-8')

                    payload = jwt.decode(
                        token,
                        public_pem,
                        algorithms=["RS256"],
                        audience=settings.AUTH0_API_IDENTIFIER,
                        issuer=f"https://{settings.AUTH0_DOMAIN}/"
                    )
                    logger.debug("✓ Auth0 token signature verified successfully using constructed RSA PEM")
                    logger.debug("✓ Token audience and issuer validated")
                    return payload
                except Exception as rsa_err:
                    logger.warning(f"Constructed RSA PEM verification failed: {rsa_err}")
                    # fall through to x5c fallback

        # Fallback: Extract public key from x5c (X.509 certificate)
        if signing_key and "x5c" in signing_key:
            cert_data = signing_key["x5c"][0]

            # Insert line breaks every 64 characters for proper PEM format
            cert_lines = [cert_data[i:i+64] for i in range(0, len(cert_data), 64)]
            cert_str = "-----BEGIN CERTIFICATE-----\n" + "\n".join(cert_lines) + "\n-----END CERTIFICATE-----"

            logger.debug("Formatting x5c certificate for PEM parsing (fallback)")

            try:
                cert = load_pem_x509_certificate(cert_str.encode(), default_backend())
                public_key = cert.public_key()

                # Convert public key to PEM string so python-jose can consume it safely
                public_pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode('utf-8')

                payload = jwt.decode(
                    token,
                    public_pem,
                    algorithms=["RS256"],
                    audience=settings.AUTH0_API_IDENTIFIER,
                    issuer=f"https://{settings.AUTH0_DOMAIN}/"
                )

                logger.debug("✓ Auth0 token signature verified successfully using x5c PEM")
                logger.debug("✓ Token audience and issuer validated")
                return payload
            except JWTError as e:
                logger.error(f"❌ Auth0 token validation failed using x5c PEM: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Could not validate token: {str(e)}"
                )
            except Exception as cert_error:
                logger.error(f"❌ Failed to parse x5c certificate fallback: {str(cert_error)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token validation failed: {str(cert_error)}"
                )

        # If we reach here, no usable key was found
        logger.error("No usable signing key found for token verification")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No signing key available for token verification"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Auth0 token validation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )


# ============================================================================
# Local JWT Token Management
# ============================================================================



def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    if additional_claims:
        to_encode.update(additional_claims)

    logger.info(f"Creating access token for subject: {subject}")
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(subject: str) -> str:
    """Create a JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token (Auth0 or local)."""
    USE_AUTH0 = True
    logger.info(f"Decoding token...{token} USE_AUTH0={USE_AUTH0}")
    if USE_AUTH0:
        logger.debug("🔍 Attempting Auth0 token validation...")
        return decode_auth0_token(token)
    else:
        # Local JWT validation
        logger.debug(f"🔍 Attempting local JWT token validation...{token}")
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            logger.debug("✓ Local JWT token validated successfully")
            return payload
        except JWTError as e:
            logger.error(f"❌ Local JWT validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )


async def get_current_user(
    request: Request
) -> dict:
    """Get the current authenticated user from the JWT token.

    Token source priority:
    1. Authorization header (Bearer token)
    2. auth_token cookie (httpOnly)
    """
    # Try Authorization header first
    auth_header = request.headers.get('authorization')
    token = None
    # loop through request headers to find the authorization header in a case-insensitive way


    logger.info(f"Extracting token from request...{auth_header}")
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]
            logger.debug('Using token from Authorization header')
        else:
            logger.debug('Malformed Authorization header')

    # Fallback to httpOnly cookie
    if not token:
        cookie_token = request.cookies.get('auth_token')
        if cookie_token:
            token = cookie_token
            logger.debug('Using token from auth_token cookie')

    if not token:
        logger.warning('No authentication token provided')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not authenticated',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    payload = decode_token(token)
    logger.info(f"Extracting user info from payload...{payload}")
    if USE_AUTH0:
        # Auth0 token structure
        user_id = payload.get('sub')
        if not user_id:
            logger.error('❌ Auth0 token validation failed: Missing user ID')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate credentials'
            )

        # Extract roles from Auth0 custom claim: prefer namespaced claim, fallback to 'roles'
        roles = payload.get('https://nexusguard.com/roles') or payload.get('roles') or []
        if isinstance(roles, str):
            roles = [roles]
        elif not roles:
            roles = ['viewer']  # Default role

        # Use first role as primary role
        primary_role = roles[0] if roles else 'viewer'

        user_info = {
            'id': user_id,
            'email': payload.get('email'),
            'name': payload.get('name'),
            'role': primary_role,
            'roles': roles,
            'exp': payload.get('exp'),
            'auth_method': 'auth0'
        }

        # Log user details
        logger.info('=' * 60)
        logger.info('✓ AUTH0 USER AUTHENTICATED')
        logger.info('=' * 60)
        logger.info(f"User ID: {user_info['id']}")
        logger.info(f"Email: {user_info['email']}")
        logger.info(f"Name: {user_info['name']}")
        logger.info(f"Primary Role: {user_info['role']}")
        logger.info(f"All Roles: {user_info['roles']}")
        logger.info(f"Token Expiry: {user_info['exp']}")
        logger.info(f"Auth Method: {user_info['auth_method']}")
        logger.info('=' * 60)

        return user_info
    else:

        user_id = payload.get('sub')
        if user_id is None:
            logger.error('❌ Local JWT validation failed: Missing user ID')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate credentials',
                headers={'WWW-Authenticate': 'Bearer'},
            )

        # Local token uses simple 'role' claim
        user_info = {
            'id': user_id,
            'role': payload.get('role', 'viewer'),
            'region': payload.get('region'),
            'exp': payload.get('exp'),
            'auth_method': 'local'
        }

        # Log user details
        logger.info('=' * 60)
        logger.info('✓ LOCAL JWT USER AUTHENTICATED')
        logger.info('=' * 60)
        logger.info(f"User ID: {user_info['id']}")
        logger.info(f"Role: {user_info['role']}")
        logger.info(f"Region: {user_info['region']}")
        logger.info(f"Token Expiry: {user_info['exp']}")
        logger.info(f"Auth Method: {user_info['auth_method']}")
        logger.info('=' * 60)

        return user_info


class RoleChecker:
    """Dependency class to check user roles (supports Auth0 and local JWT)."""

    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: dict = Depends(get_current_user)) -> dict:
        # Check role based on authentication method
        if user.get("auth_method") == "auth0":
            # For Auth0, check if any user role is in allowed roles
            user_roles = user.get("roles", [])
            if not any(role in self.allowed_roles for role in user_roles):
                logger.warning(f"❌ Access denied: User {user.get('id')} with roles {user_roles} attempted to access endpoint requiring {self.allowed_roles}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for this operation"
                )
            logger.info(f"✓ Access granted: User {user.get('id')} with roles {user_roles} authorized for endpoint")
        else:
            # For local JWT, check single role
            user_role = user.get("role")
            if user_role not in self.allowed_roles:
                logger.warning(f"❌ Access denied: User {user.get('id')} with role {user_role} attempted to access endpoint requiring {self.allowed_roles}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            logger.info(f"✓ Access granted: User {user.get('id')} with role {user_role} authorized for endpoint")

        return user


# Role-based access control dependencies
require_admin = RoleChecker(["admin"])
require_noc_engineer = RoleChecker(["admin", "noc_engineer"])
require_viewer = RoleChecker(["admin", "noc_engineer", "viewer"])
