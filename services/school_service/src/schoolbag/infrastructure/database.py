"""Database schemas, initialization, and connection wrappers for SQLite and PostgreSQL."""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager, suppress
from typing import Any


class ConnectionWrapper:
    """Wraps sqlite3 or psycopg connection to adapt queries transparently."""

    def __init__(self, raw_conn: Any, is_postgres: bool = False) -> None:
        self.raw_conn = raw_conn
        self.is_postgres = is_postgres

    def cursor(self) -> CursorWrapper:
        raw_cur = self.raw_conn.cursor()
        return CursorWrapper(raw_cur, self.is_postgres)

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] | None = None) -> CursorWrapper:
        cur = self.cursor()
        return cur.execute(sql, params)

    def commit(self) -> None:
        self.raw_conn.commit()

    def rollback(self) -> None:
        self.raw_conn.rollback()

    def close(self) -> None:
        self.raw_conn.close()

    def __enter__(self) -> ConnectionWrapper:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            self.rollback()
        else:
            self.commit()


class CursorWrapper:
    """Wraps cursor to adapt ? to %s on PostgreSQL."""

    def __init__(self, raw_cur: Any, is_postgres: bool = False) -> None:
        self.raw_cur = raw_cur
        self.is_postgres = is_postgres

    @property
    def rowcount(self) -> int:
        return self.raw_cur.rowcount  # type: ignore[no-any-return]

    @property
    def lastrowid(self) -> Any:
        return getattr(self.raw_cur, "lastrowid", None)

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] | None = None) -> CursorWrapper:
        adapted_sql = self._adapt_sql(sql)
        if params is None:
            self.raw_cur.execute(adapted_sql)
        else:
            self.raw_cur.execute(adapted_sql, params)
        return self

    def executemany(self, sql: str, seq_of_params: Any) -> CursorWrapper:
        adapted_sql = self._adapt_sql(sql)
        self.raw_cur.executemany(adapted_sql, seq_of_params)
        return self

    def fetchone(self) -> Any:
        return self.raw_cur.fetchone()

    def fetchall(self) -> list[Any]:
        return self.raw_cur.fetchall()  # type: ignore[no-any-return]

    def close(self) -> None:
        self.raw_cur.close()

    def _adapt_sql(self, sql: str) -> str:
        if not self.is_postgres:
            return sql
        # Adapt ? placeholders to %s for psycopg
        return sql.replace("?", "%s")


SQLITE_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS workspaces (
    workspace_id TEXT PRIMARY KEY,
    session_token TEXT NOT NULL UNIQUE,
    notice_count INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notices (
    notice_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    class_name TEXT NOT NULL,
    child_alias TEXT NOT NULL,
    title TEXT NOT NULL,
    raw_body TEXT NOT NULL,
    raw_due_text TEXT,
    normalized_due_at TEXT,
    source_fingerprint TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS actions (
    action_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    notice_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    raw_deadline TEXT,
    normalized_deadline TEXT,
    amount_inr REAL,
    status TEXT NOT NULL,
    approval_required INTEGER NOT NULL DEFAULT 0,
    approved_by TEXT,
    approved_at TEXT,
    completed_by TEXT,
    completed_at TEXT,
    confidence REAL NOT NULL DEFAULT 1.0,
    extraction_provenance TEXT NOT NULL DEFAULT '{}',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    FOREIGN KEY(notice_id) REFERENCES notices(notice_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reminder_drafts (
    reminder_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    notice_id TEXT NOT NULL,
    title TEXT NOT NULL,
    channel TEXT NOT NULL,
    scheduled_for TEXT NOT NULL,
    message_body TEXT NOT NULL,
    is_draft INTEGER NOT NULL DEFAULT 1,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    FOREIGN KEY(action_id) REFERENCES actions(action_id) ON DELETE CASCADE,
    FOREIGN KEY(notice_id) REFERENCES notices(notice_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_name TEXT NOT NULL,
    version_before INTEGER NOT NULL,
    version_after INTEGER NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS idempotency_records (
    workspace_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_body TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (workspace_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS inference_admissions (
    reservation_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    request_key_hash TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    reserved_sends INTEGER NOT NULL DEFAULT 6,
    deadline_at TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'RESERVED',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    dispatched_at TEXT,
    completed_at TEXT,
    released_at TEXT,
    actual_sends INTEGER,
    actual_total_tokens INTEGER,
    cleanup_completed INTEGER,
    failure_code TEXT,
    recovery_operator_id TEXT,
    recovery_reason TEXT,
    recovered_at TEXT,
    response_body TEXT
);

CREATE INDEX IF NOT EXISTS idx_notices_ws_fp ON notices(workspace_id, source_fingerprint);
CREATE INDEX IF NOT EXISTS idx_actions_ws_notice ON actions(workspace_id, notice_id);
CREATE INDEX IF NOT EXISTS idx_reminders_ws_action ON reminder_drafts(workspace_id, action_id);
CREATE INDEX IF NOT EXISTS idx_audit_ws_entity ON audit_events(workspace_id, entity_id);
CREATE INDEX IF NOT EXISTS idx_workspaces_token ON workspaces(session_token);
CREATE INDEX IF NOT EXISTS idx_admissions_workspace_key ON inference_admissions(workspace_id, request_key_hash);
CREATE INDEX IF NOT EXISTS idx_admissions_cooldown ON inference_admissions(failure_code, completed_at);
CREATE INDEX IF NOT EXISTS idx_admissions_created ON inference_admissions(created_at);
CREATE INDEX IF NOT EXISTS idx_admissions_active ON inference_admissions(is_active);
CREATE UNIQUE INDEX IF NOT EXISTS ux_inference_admissions_single_active ON inference_admissions(is_active) WHERE is_active = 1;
"""


def init_db(raw_conn: Any, is_postgres: bool = False) -> None:
    """Initialize database schema on connection with engine adaptation."""
    cur = raw_conn.cursor()
    if is_postgres:
        schema = re.sub(r"^PRAGMA\s+.*?;", "", SQLITE_SCHEMA, flags=re.MULTILINE | re.IGNORECASE)
        # Execute statement by statement
        for stmt in schema.split(";"):
            clean = stmt.strip()
            if clean:
                cur.execute(clean)
        raw_conn.commit()
    else:
        # SQLite executes entire script
        raw_conn.executescript(SQLITE_SCHEMA)
        raw_conn.commit()


@contextmanager
def get_db_connection(
    db_target: str, write: bool = False
) -> Generator[ConnectionWrapper, None, None]:
    """Provide a transactional scope around SQLite or PostgreSQL operations."""
    if db_target.startswith(("postgresql://", "postgres://")):
        norm_url = db_target
        if norm_url.startswith("postgres://"):
            norm_url = "postgresql://" + norm_url[len("postgres://") :]
        import psycopg
        from psycopg.rows import dict_row

        pg_conn = psycopg.connect(norm_url, row_factory=dict_row, connect_timeout=10)
        try:
            with pg_conn.transaction():
                yield ConnectionWrapper(pg_conn, is_postgres=True)
        finally:
            pg_conn.close()
    else:
        db_path = db_target.replace("sqlite:///", "")
        sqlite_conn = sqlite3.connect(db_path, timeout=15.0, isolation_level=None)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_conn.execute("PRAGMA foreign_keys = ON;")
        if write:
            try:
                if not sqlite_conn.in_transaction:
                    sqlite_conn.execute("BEGIN IMMEDIATE;")
                yield ConnectionWrapper(sqlite_conn, is_postgres=False)
                if sqlite_conn.in_transaction:
                    sqlite_conn.execute("COMMIT;")
            except Exception:
                with suppress(Exception):
                    if sqlite_conn.in_transaction:
                        sqlite_conn.execute("ROLLBACK;")
                raise
            finally:
                sqlite_conn.close()
        else:
            try:
                yield ConnectionWrapper(sqlite_conn, is_postgres=False)
            finally:
                sqlite_conn.close()
