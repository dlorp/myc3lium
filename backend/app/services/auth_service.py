"""
Authentication service for myc3lium multi-user platform.

Handles user CRUD, password hashing (argon2id), JWT token management,
session tracking, and node-to-user binding.
"""

from __future__ import annotations

import logging
import re
import secrets
import threading
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import argon2
import jwt

from app.db import get_connection

logger = logging.getLogger(__name__)

_hasher = argon2.PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64MB — reasonable for Pi
    parallelism=1,
)

# Token lifetimes
_BROWSER_TOKEN_HOURS = 24
_HANDHELD_TOKEN_DAYS = 7
_REFRESH_WINDOW_HOURS = 4


class AuthError(Exception):
    """Authentication error with user-safe message."""

    def __init__(self, message: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ---- JWT ----

_jwt_secret_cache: str | None = None
_jwt_secret_lock = threading.Lock()


def _get_jwt_secret() -> str:
    """Read JWT secret from config service, generating if empty. Thread-safe cached."""
    global _jwt_secret_cache
    if _jwt_secret_cache is not None:
        return _jwt_secret_cache

    with _jwt_secret_lock:
        if _jwt_secret_cache is not None:
            return _jwt_secret_cache

        from app.services.config_service import ConfigService

        svc = ConfigService()
        secret = svc.config.system.jwt_secret
        if not secret:
            secret = secrets.token_hex(32)
            svc.update_section("system", {"jwt_secret": secret})
            logger.info("Generated new JWT secret")
        _jwt_secret_cache = secret
        return secret


def mint_token(
    user: dict[str, Any],
    session_id: str,
    *,
    handheld: bool = False,
) -> str:
    """Mint a JWT token for a user session."""
    now = _now()
    if handheld:
        expires = now + timedelta(days=_HANDHELD_TOKEN_DAYS)
    else:
        expires = now + timedelta(hours=_BROWSER_TOKEN_HOURS)

    payload = {
        "sub": user["id"],
        "username": user["username"],
        "callsign": user["callsign"],
        "role": user["role"],
        "node_id": user.get("node_id"),
        "handheld": handheld,
        "jti": session_id,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm="HS256")


def verify_token(token: str) -> dict[str, Any]:
    """Verify and decode a JWT token. Checks session revocation."""
    try:
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.InvalidTokenError as exc:
        raise AuthError(f"Invalid token: {exc}")

    # Require jti claim (C1 + H7: missing jti = un-revocable token)
    session_id = payload.get("jti")
    if not session_id:
        raise AuthError("Invalid token: missing session ID")

    # Check session exists and is not revoked (C1: treat missing row as revoked,
    # since cleanup task deletes expired/revoked rows)
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT revoked FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row:
            raise AuthError("Session expired or revoked")
        if row["revoked"]:
            raise AuthError("Session revoked")
    finally:
            conn.close()

    return payload


# ---- Password hashing ----

def _hash_password(password: str) -> str:
    return _hasher.hash(password)


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except argon2.exceptions.VerifyMismatchError:
        return False
    except argon2.exceptions.InvalidHashError:
        logger.error("Invalid password hash in database")
        return False


# M1: Dummy hash for constant-time response when user doesn't exist
_DUMMY_HASH = _hasher.hash("dummy-password-timing-defense")


# ---- User CRUD ----

def _validate_user_input(
    username: str, callsign: str, password: str, role: str,
) -> None:
    """Validate user creation/update inputs."""
    if role not in ("admin", "operator", "observer"):
        raise AuthError("Invalid role", status_code=400)
    if len(username) < 3 or len(username) > 32:
        raise AuthError("Username must be 3-32 characters", status_code=400)
    if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
        raise AuthError("Username must be alphanumeric, dots, hyphens, or underscores", status_code=400)
    if len(callsign) < 2 or len(callsign) > 16:
        raise AuthError("Callsign must be 2-16 characters", status_code=400)
    if not re.match(r"^[a-zA-Z0-9/_-]+$", callsign):
        raise AuthError("Callsign must be alphanumeric, slashes, hyphens, or underscores", status_code=400)
    if len(password) < 8:
        raise AuthError("Password must be at least 8 characters", status_code=400)


def create_bootstrap_user(
    username: str,
    callsign: str,
    password: str,
) -> dict[str, Any] | None:
    """Atomically create the first user as admin, only if no users exist.

    Returns None if users already exist (lost the race).
    """
    _validate_user_input(username, callsign, password, "admin")

    user_id = str(uuid4())
    now = _iso(_now())
    password_hash = _hash_password(password)

    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (id, username, callsign, password_hash, role, created_at) "
            "SELECT ?, ?, ?, ?, 'admin', ? "
            "WHERE NOT EXISTS (SELECT 1 FROM users LIMIT 1)",
            (user_id, username, callsign, password_hash, now),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None  # Someone created a user first — race lost
    except Exception as exc:
        if "UNIQUE constraint" in str(exc):
            raise AuthError("Username or callsign already exists", status_code=409)
        raise
    finally:
        conn.close()

    logger.info("Bootstrap: created first admin user %s (callsign=%s)", username, callsign)
    return {
        "id": user_id,
        "username": username,
        "callsign": callsign,
        "role": "admin",
        "node_id": None,
        "created_at": now,
        "last_login": None,
        "active": True,
    }


def create_user(
    username: str,
    callsign: str,
    password: str,
    role: str = "operator",
) -> dict[str, Any]:
    """Create a new user. Returns the user dict (without password_hash)."""
    _validate_user_input(username, callsign, password, role)

    user_id = str(uuid4())
    now = _iso(_now())
    password_hash = _hash_password(password)

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (id, username, callsign, password_hash, role, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, callsign, password_hash, role, now),
        )
        conn.commit()
    except Exception as exc:
        if "UNIQUE constraint" in str(exc):
            raise AuthError("Username or callsign already exists", status_code=409)
        raise
    finally:
        conn.close()

    logger.info("Created user %s (role=%s, callsign=%s)", username, role, callsign)
    return {
        "id": user_id,
        "username": username,
        "callsign": callsign,
        "role": role,
        "node_id": None,
        "created_at": now,
        "last_login": None,
        "active": True,
    }


def authenticate(
    username: str,
    password: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
    handheld: bool = False,
) -> tuple[dict[str, Any], str]:
    """Authenticate a user. Returns (user_dict, jwt_token)."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND active = 1",
            (username,),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        # M1: Constant-time response — prevent username enumeration via timing
        _verify_password("dummy", _DUMMY_HASH)
        raise AuthError("Invalid credentials")

    if not _verify_password(password, row["password_hash"]):
        raise AuthError("Invalid credentials")

    user = dict(row)
    del user["password_hash"]

    # Create session
    session_id = str(uuid4())
    now = _now()
    if handheld:
        expires = now + timedelta(days=_HANDHELD_TOKEN_DAYS)
    else:
        expires = now + timedelta(hours=_BROWSER_TOKEN_HOURS)

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO sessions (id, user_id, created_at, expires_at, ip_address, user_agent) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, user["id"], _iso(now), _iso(expires), ip_address, user_agent),
        )
        conn.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (_iso(now), user["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    token = mint_token(user, session_id, handheld=handheld)
    logger.info("User %s authenticated (session=%s)", username, session_id[:8])
    return user, token


def revoke_session(session_id: str) -> None:
    """Revoke a session (logout)."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE sessions SET revoked = 1 WHERE id = ?", (session_id,)
        )
        conn.commit()
    finally:
        conn.close()


def refresh_token(token: str) -> str | None:
    """Refresh a token if within the refresh window. Returns new token or None."""
    payload = verify_token(token)
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = _now()

    # Only refresh if within the last N hours of token life
    refresh_start = exp - timedelta(hours=_REFRESH_WINDOW_HOURS)
    if now < refresh_start:
        return None  # Too early to refresh

    # Revoke old session, create new one
    old_session_id = payload.get("jti")
    if old_session_id:
        revoke_session(old_session_id)

    user = get_user(payload["sub"])
    if not user:
        return None

    # H6: Preserve handheld token type through refresh
    is_handheld = payload.get("handheld", False)
    session_id = str(uuid4())
    if is_handheld:
        expires = now + timedelta(days=_HANDHELD_TOKEN_DAYS)
    else:
        expires = now + timedelta(hours=_BROWSER_TOKEN_HOURS)

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO sessions (id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, user["id"], _iso(now), _iso(expires)),
        )
        conn.commit()
    finally:
        conn.close()

    return mint_token(user, session_id, handheld=is_handheld)


def get_user(user_id: str) -> dict[str, Any] | None:
    """Get a user by ID."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, username, callsign, role, node_id, created_at, last_login, active "
            "FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_users() -> list[dict[str, Any]]:
    """List all users (without password hashes)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, username, callsign, role, node_id, created_at, last_login, active "
            "FROM users ORDER BY created_at"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


_UPDATABLE_COLUMNS = frozenset({"callsign", "role", "active", "password_hash"})


def update_user(user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Update user fields. Returns updated user or None if not found."""
    allowed = {"callsign", "role", "active"}
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if "password" in updates and updates["password"]:
        filtered["password_hash"] = _hash_password(updates["password"])

    if not filtered:
        return get_user(user_id)

    # C5: Defense-in-depth — assert all keys are known column names
    if not filtered.keys() <= _UPDATABLE_COLUMNS:
        raise AuthError("Invalid update fields", status_code=400)

    set_clause = ", ".join(f"{k} = ?" for k in filtered)
    values = list(filtered.values()) + [user_id]

    conn = get_connection()
    try:
        conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)  # noqa: S608
        conn.commit()
    finally:
        conn.close()

    return get_user(user_id)


def deactivate_user(user_id: str) -> bool:
    """Deactivate a user and revoke all their sessions."""
    conn = get_connection()
    try:
        # H3: Revoke all sessions so existing tokens become invalid immediately
        conn.execute(
            "UPDATE sessions SET revoked = 1 WHERE user_id = ?", (user_id,)
        )
        cursor = conn.execute(
            "UPDATE users SET active = 0 WHERE id = ?", (user_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def user_count() -> int:
    """Count active users (for first-user bootstrap check)."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


# ---- Node bindings ----

def bind_node(user_id: str, node_id: str, binding_type: str = "manual") -> None:
    """Bind a mesh node to a user."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO node_bindings (node_id, user_id, bound_at, binding_type) "
            "VALUES (?, ?, ?, ?)",
            (node_id, user_id, _iso(_now()), binding_type),
        )
        # M6: Clear stale node_id on any previous owner
        conn.execute(
            "UPDATE users SET node_id = NULL WHERE node_id = ? AND id != ?",
            (node_id, user_id),
        )
        conn.execute(
            "UPDATE users SET node_id = ? WHERE id = ?", (node_id, user_id)
        )
        conn.commit()
    finally:
        conn.close()
    logger.info("Bound node %s to user %s (type=%s)", node_id, user_id, binding_type)


def get_user_for_node(node_id: str) -> dict[str, Any] | None:
    """Get the user bound to a mesh node."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT u.id, u.username, u.callsign, u.role "
            "FROM node_bindings nb JOIN users u ON nb.user_id = u.id "
            "WHERE nb.node_id = ?",
            (node_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def cleanup_expired_sessions() -> int:
    """Remove expired sessions. Returns count removed."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM sessions WHERE expires_at < ? OR revoked = 1",
            (_iso(_now()),),
        )
        conn.commit()
        count = cursor.rowcount
        if count > 0:
            logger.info("Cleaned up %d expired/revoked sessions", count)
        return count
    finally:
        conn.close()
