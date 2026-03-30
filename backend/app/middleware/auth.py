"""
Authentication middleware for FastAPI.

Extracts JWT from Authorization header or ?token= query param (WebSocket).
When require_auth is false (default), allows anonymous access with a synthetic user.
Legacy X-API-Key header is still accepted when MESHTASTIC_API_KEY env var is set.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, Header, Query, Request

from app.services.auth_service import AuthError, verify_token

logger = logging.getLogger(__name__)


class AnonymousUser:
    """Synthetic user for unauthenticated access when auth is not required."""

    id = "anonymous"
    username = "anonymous"
    callsign = "ANON"
    role = "admin"  # Full access when auth is disabled
    node_id = None
    is_anonymous = True


def _auth_required() -> bool:
    """Check if auth is required from config."""
    try:
        from app.services.config_service import ConfigService

        svc = ConfigService()
        return svc.config.system.require_auth
    except Exception:
        return False


async def get_current_user(
    request: Request,
    authorization: str | None = Header(None),
    token: str | None = Query(None),
) -> dict[str, Any] | AnonymousUser:
    """FastAPI dependency that extracts and validates the current user.

    Token sources (checked in order):
    1. Authorization: Bearer <token> header
    2. ?token=<token> query parameter (for WebSocket connections)

    When require_auth is False, returns AnonymousUser if no token is provided.
    """
    jwt_token = None

    # Extract from Authorization header
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization[7:]

    # Fall back to query param (WebSocket)
    if not jwt_token and token:
        jwt_token = token

    if jwt_token:
        try:
            payload = verify_token(jwt_token)
            return {
                "id": payload["sub"],
                "username": payload["username"],
                "callsign": payload["callsign"],
                "role": payload["role"],
                "node_id": payload.get("node_id"),
                "jti": payload.get("jti"),
                "is_anonymous": False,
            }
        except AuthError as exc:
            if _auth_required():
                from fastapi import HTTPException

                raise HTTPException(status_code=exc.status_code, detail=exc.message)
            # Auth not required — fall through to anonymous
            logger.debug("Invalid token but auth not required: %s", exc.message)

    if _auth_required():
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Authentication required")

    return AnonymousUser()


def require_role(*roles: str):
    """Dependency factory that requires the user to have one of the specified roles."""

    async def check_role(
        user: dict[str, Any] | AnonymousUser = Depends(get_current_user),
    ) -> dict[str, Any] | AnonymousUser:
        if isinstance(user, AnonymousUser):
            return user  # Anonymous has admin role when auth is disabled

        user_role = user.get("role", "observer")
        if user_role not in roles:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=403,
                detail=f"Requires role: {', '.join(roles)}",
            )
        return user

    return check_role
