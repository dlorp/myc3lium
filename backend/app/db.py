"""
SQLite database for myc3lium user authentication.

Uses WAL mode for concurrent read/write from WebSocket + REST handlers.
Production: /opt/myc3lium/data/myc3lium.db
Development: ./myc3lium.db
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

_DB_PATH_PROD = Path("/opt/myc3lium/data/myc3lium.db")
_DB_PATH_DEV = Path("./myc3lium.db")

_SCHEMA_VERSION = 1

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    callsign      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'operator',
    node_id       TEXT,
    created_at    TEXT NOT NULL,
    last_login    TEXT,
    active        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked    INTEGER NOT NULL DEFAULT 0,
    ip_address TEXT,
    user_agent TEXT
);

CREATE TABLE IF NOT EXISTS node_bindings (
    node_id      TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL REFERENCES users(id),
    bound_at     TEXT NOT NULL,
    binding_type TEXT NOT NULL DEFAULT 'manual',
    last_seen    TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_node_bindings_user ON node_bindings(user_id);
"""


def _db_path() -> Path:
    if settings.use_live_data:
        _DB_PATH_PROD.parent.mkdir(parents=True, exist_ok=True)
        return _DB_PATH_PROD
    return _DB_PATH_DEV


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode and row factory."""
    conn = sqlite3.connect(str(_db_path()), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Initialize the database schema if needed."""
    conn = get_connection()
    try:
        conn.executescript(_SCHEMA_SQL)

        # Check/set schema version
        row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (_SCHEMA_VERSION,),
            )
        conn.commit()
        logger.info(
            "Auth database initialized at %s (v%d)", _db_path(), _SCHEMA_VERSION
        )
    except Exception:
        logger.exception("Failed to initialize auth database")
        raise
    finally:
        conn.close()
