"""Authentication API endpoints."""
from fastapi import APIRouter, HTTPException, status
from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    decode_token,
)
from app.core.config import settings
from app.models.schemas import Token, UserCreate, User
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Demo users (replace with database in production)
DEMO_USERS = {
    "admin@nexusguard.io": {
        "id": "user-001",
        "email": "admin@nexusguard.io",
        "username": "admin",
        "full_name": "NOC Administrator",
        "role": "admin",
        "region": None,
        "password_hash": get_password_hash("admin123"),
        "is_active": True
    },
    "engineer@nexusguard.io": {
        "id": "user-002",
        "email": "engineer@nexusguard.io",
        "username": "noc_engineer",
        "full_name": "NOC Engineer",
        "role": "noc_engineer",
        "region": "usa",
        "password_hash": get_password_hash("engineer123"),
        "is_active": True
    },
    "viewer@nexusguard.io": {
        "id": "user-003",
        "email": "viewer@nexusguard.io",
        "username": "viewer",
        "full_name": "Dashboard Viewer",
        "role": "viewer",
        "region": None,
        "password_hash": get_password_hash("viewer123"),
        "is_active": True
    }
}


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Authenticate user and return JWT tokens."""
    user = DEMO_USERS.get(request.email)

    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )

    # Create tokens with user claims
    access_token = create_access_token(
        subject=user["id"],
        additional_claims={
            "role": user["role"],
            "region": user["region"],
            "email": user["email"]
        }
    )
    refresh_token = create_refresh_token(subject=user["id"])

    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshRequest):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user_id = payload.get("sub")

    # Find user
    user = None
    for u in DEMO_USERS.values():
        if u["id"] == user_id:
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Create new tokens
    access_token = create_access_token(
        subject=user["id"],
        additional_claims={
            "role": user["role"],
            "region": user["region"],
            "email": user["email"]
        }
    )
    new_refresh_token = create_refresh_token(subject=user["id"])

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token
    )


@router.get("/me")
async def get_current_user_info():
    """Get information about available demo users."""
    return {
        "demo_users": [
            {
                "email": "admin@nexusguard.io",
                "password": "admin123",
                "role": "admin"
            },
            {
                "email": "engineer@nexusguard.io",
                "password": "engineer123",
                "role": "noc_engineer"
            },
            {
                "email": "viewer@nexusguard.io",
                "password": "viewer123",
                "role": "viewer"
            }
        ]
    }
