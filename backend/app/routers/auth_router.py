"""
Authentication API endpoints.

Handles login, logout, token refresh, and user management (admin).
First-user bootstrap: when no users exist, the first POST /api/auth/users
does not require authentication.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.middleware.auth import AnonymousUser, get_current_user, require_role
from app.rate_limit import login_limiter
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---- Request/Response models ----


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=8)
    handheld: bool = Field(
        False, description="Request long-lived token for handheld device"
    )


class LoginResponse(BaseModel):
    token: str
    user: dict[str, Any]


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    callsign: str = Field(..., min_length=2, max_length=16)
    password: str = Field(..., min_length=8)
    role: str = Field("operator", pattern=r"^(admin|operator|observer)$")


class UpdateUserRequest(BaseModel):
    callsign: str | None = Field(None, min_length=2, max_length=16)
    role: str | None = Field(None, pattern=r"^(admin|operator|observer)$")
    password: str | None = Field(None, min_length=8)
    active: bool | None = None


class BindNodeRequest(BaseModel):
    node_id: str = Field(..., min_length=1, max_length=64)
    binding_type: str = Field("manual", pattern=r"^(manual|auto|certificate)$")


class RefreshRequest(BaseModel):
    token: str


# ---- Endpoints ----


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    _rate_limit: bool = Depends(login_limiter),
) -> LoginResponse:
    """Authenticate and receive a JWT token."""
    try:
        # H4: Run argon2 hashing in threadpool to avoid blocking the event loop
        user, token = await run_in_threadpool(
            auth_service.authenticate,
            body.username,
            body.password,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            handheld=body.handheld,
        )
        return LoginResponse(token=token, user=user)
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/logout")
async def logout(
    user: dict[str, Any] | AnonymousUser = Depends(get_current_user),
) -> dict[str, str]:
    """Revoke the current session."""
    if isinstance(user, AnonymousUser):
        return {"message": "Not authenticated"}
    session_id = user.get("jti")
    if session_id:
        auth_service.revoke_session(session_id)
    return {"message": "Logged out"}


@router.post("/refresh")
async def refresh(body: RefreshRequest) -> dict[str, str | None]:
    """Refresh a token if within the refresh window."""
    try:
        new_token = auth_service.refresh_token(body.token)
        if new_token:
            return {"token": new_token}
        return {"token": None, "message": "Token not yet eligible for refresh"}
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/me")
async def get_me(
    user: dict[str, Any] | AnonymousUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Get current user info. Also reports whether auth is required."""
    from app.middleware.auth import _auth_required

    if isinstance(user, AnonymousUser):
        return {
            "authenticated": False,
            "auth_required": _auth_required(),
            "user": None,
        }
    return {
        "authenticated": True,
        "auth_required": _auth_required(),
        "user": user,
    }


@router.get("/users")
async def list_users(
    _user: dict[str, Any] | AnonymousUser = Depends(require_role("admin")),
) -> list[dict[str, Any]]:
    """List all users (admin only)."""
    return auth_service.list_users()


@router.post("/users", status_code=201)
async def create_user(
    body: CreateUserRequest,
    user: dict[str, Any] | AnonymousUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a new user.

    First-user bootstrap: when no users exist, this endpoint
    does not require authentication and creates an admin.
    """
    # C4: Atomic bootstrap — no TOCTOU race
    if auth_service.user_count() == 0:
        try:
            new_user = auth_service.create_bootstrap_user(
                body.username, body.callsign, body.password
            )
            if new_user is None:
                # Lost the race — someone else created a user first
                raise HTTPException(status_code=403, detail="Admin role required")
            return new_user
        except auth_service.AuthError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message)

    # Require admin role for subsequent user creation
    if isinstance(user, AnonymousUser) or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    try:
        new_user = auth_service.create_user(
            body.username, body.callsign, body.password, body.role
        )
        return new_user
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    _user: dict[str, Any] | AnonymousUser = Depends(require_role("admin")),
) -> dict[str, Any]:
    """Update a user (admin only)."""
    updates = body.model_dump(exclude_none=True)
    result = auth_service.update_user(user_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    _user: dict[str, Any] | AnonymousUser = Depends(require_role("admin")),
) -> dict[str, str]:
    """Deactivate a user (admin only, soft delete)."""
    # H5: Prevent admin from deactivating themselves
    if not isinstance(_user, AnonymousUser) and _user.get("id") == user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    # H5: Prevent removing the last active admin
    users = auth_service.list_users()
    active_admins = [
        u for u in users if u["role"] == "admin" and u["active"] and u["id"] != user_id
    ]
    if not active_admins:
        raise HTTPException(status_code=400, detail="Cannot deactivate the last admin")

    if auth_service.deactivate_user(user_id):
        return {"message": "User deactivated"}
    raise HTTPException(status_code=404, detail="User not found")


@router.post("/users/{user_id}/bind-node")
async def bind_node(
    user_id: str,
    body: BindNodeRequest,
    _user: dict[str, Any] | AnonymousUser = Depends(require_role("admin")),
) -> dict[str, str]:
    """Bind a mesh node to a user (admin only)."""
    target = auth_service.get_user(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    auth_service.bind_node(user_id, body.node_id, body.binding_type)
    return {"message": f"Node {body.node_id} bound to {target['username']}"}
