"""Persistent dual SQLite/PostgreSQL store for Schoolbag."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from schoolbag.domain.errors import (
    ActionNotFoundError,
    CapacityExceededError,
    IdempotencyConflictError,
    StateConflictError,
)
from schoolbag.domain.models import (
    ActionStatus,
    AuditEvent,
    Notice,
    NoticeAggregate,
    ReminderDraft,
    SchoolAction,
    Workspace,
)
from schoolbag.domain.workflow import (
    enforce_human_approval_gate,
    validate_action_transition,
)
from schoolbag.infrastructure.database import ConnectionWrapper, init_db


class SqliteSchoolbagStore:
    """Thread-safe persistent store supporting SQLite and PostgreSQL with atomic operations."""

    def __init__(
        self,
        db_path: str = "schoolbag.db",
        is_postgres: bool = False,
        raw_conn_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.db_path = db_path
        self.is_postgres = is_postgres
        self.raw_conn_factory = raw_conn_factory
        self._lock = threading.RLock()

        # Initialize schema
        with self._get_connection() as conn:
            init_db(conn.raw_conn, is_postgres=self.is_postgres)

    def _get_connection(self) -> ConnectionWrapper:
        if self.raw_conn_factory:
            raw_conn = self.raw_conn_factory()
            return ConnectionWrapper(raw_conn, is_postgres=self.is_postgres)
        if self.is_postgres:
            import psycopg

            raw_conn = psycopg.connect(self.db_path)
            return ConnectionWrapper(raw_conn, is_postgres=True)
        # SQLite
        raw_conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        raw_conn.row_factory = sqlite3.Row
        raw_conn.execute("PRAGMA journal_mode=WAL;")
        raw_conn.execute("PRAGMA foreign_keys=ON;")
        return ConnectionWrapper(raw_conn, is_postgres=False)

    def get_or_create_workspace(self, session_token: str) -> Workspace:
        """Find active workspace by session token or create a new one with 30-day TTL."""
        now = datetime.now(UTC)
        now_str = now.isoformat()
        expires_str = (now + timedelta(days=30)).isoformat()

        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT workspace_id, session_token, notice_count, is_active, created_at, updated_at, expires_at "
                "FROM workspaces WHERE session_token = ?",
                (session_token,),
            )
            row = cur.fetchone()
            if row:
                ws = Workspace(
                    workspace_id=row[0],
                    session_token=row[1],
                    notice_count=row[2],
                    is_active=bool(row[3]),
                    created_at=row[4],
                    updated_at=now_str,
                    expires_at=row[6],
                )
                cur.execute(
                    "UPDATE workspaces SET updated_at = ? WHERE workspace_id = ?",
                    (now_str, ws.workspace_id),
                )
                return ws

            # Check global active workspace capacity (1,000 max)
            cur.execute("SELECT COUNT(*) FROM workspaces WHERE is_active = 1")
            cnt_row = cur.fetchone()
            global_count = cnt_row[0] if cnt_row else 0
            if global_count >= 1000:
                raise CapacityExceededError(
                    "Global active workspace capacity reached (1,000 workspaces).",
                    limit=1000,
                    current=global_count,
                )

            ws_id = f"ws_{uuid.uuid4().hex[:12]}"
            cur.execute(
                "INSERT INTO workspaces (workspace_id, session_token, notice_count, is_active, created_at, updated_at, expires_at) "
                "VALUES (?, ?, 0, 1, ?, ?, ?)",
                (ws_id, session_token, now_str, now_str, expires_str),
            )
            return Workspace(
                workspace_id=ws_id,
                session_token=session_token,
                notice_count=0,
                is_active=True,
                created_at=now_str,
                updated_at=now_str,
                expires_at=expires_str,
            )

    def get_workspace_by_id(self, workspace_id: str) -> Workspace | None:
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT workspace_id, session_token, notice_count, is_active, created_at, updated_at, expires_at "
                "FROM workspaces WHERE workspace_id = ?",
                (workspace_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return Workspace(
                workspace_id=row[0],
                session_token=row[1],
                notice_count=row[2],
                is_active=bool(row[3]),
                created_at=row[4],
                updated_at=row[5],
                expires_at=row[6],
            )

    def create_notice(
        self,
        notice: Notice,
        actions: list[SchoolAction],
        idempotency_key: str | None = None,
        payload_hash: str | None = None,
    ) -> tuple[Notice, list[SchoolAction]]:
        """Atomically create notice and its extracted actions, with deduplication and idempotency."""
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()

            # 1. Idempotency replay check
            if idempotency_key:
                cur.execute(
                    "SELECT payload_hash, response_body FROM idempotency_records "
                    "WHERE workspace_id = ? AND idempotency_key = ?",
                    (notice.workspace_id, idempotency_key),
                )
                idemp_row = cur.fetchone()
                if idemp_row:
                    stored_hash, body_json = idemp_row[0], idemp_row[1]
                    if payload_hash and stored_hash != payload_hash:
                        raise IdempotencyConflictError(idempotency_key)
                    # Replay cached result
                    data = json.loads(body_json)
                    n_data = data.get("notice", {})
                    actions_data = data.get("actions", [])
                    replayed_notice = Notice(**n_data)
                    replayed_actions = [SchoolAction(**a) for a in actions_data]
                    return replayed_notice, replayed_actions

            # 2. Deduplication check: existing notice with same content fingerprint in workspace
            cur.execute(
                "SELECT notice_id, workspace_id, source_type, class_name, child_alias, title, "
                "raw_body, raw_due_text, normalized_due_at, source_fingerprint, version, created_at, updated_at "
                "FROM notices WHERE workspace_id = ? AND source_fingerprint = ?",
                (notice.workspace_id, notice.source_fingerprint),
            )
            existing_row = cur.fetchone()
            if existing_row:
                existing_notice = Notice(
                    notice_id=existing_row[0],
                    workspace_id=existing_row[1],
                    source_type=existing_row[2],
                    class_name=existing_row[3],
                    child_alias=existing_row[4],
                    title=existing_row[5],
                    raw_body=existing_row[6],
                    raw_due_text=existing_row[7],
                    normalized_due_at=existing_row[8],
                    source_fingerprint=existing_row[9],
                    version=existing_row[10],
                    created_at=existing_row[11],
                    updated_at=existing_row[12],
                )
                # Fetch existing actions
                cur.execute(
                    "SELECT action_id, workspace_id, notice_id, action_type, title, description, "
                    "raw_deadline, normalized_deadline, amount_inr, status, approval_required, "
                    "approved_by, approved_at, completed_by, completed_at, confidence, "
                    "extraction_provenance, version, created_at, updated_at "
                    "FROM actions WHERE workspace_id = ? AND notice_id = ?",
                    (notice.workspace_id, existing_notice.notice_id),
                )
                existing_actions = [
                    SchoolAction(
                        action_id=r[0],
                        workspace_id=r[1],
                        notice_id=r[2],
                        action_type=r[3],
                        title=r[4],
                        description=r[5],
                        raw_deadline=r[6],
                        normalized_deadline=r[7],
                        amount_inr=r[8],
                        status=r[9],
                        approval_required=bool(r[10]),
                        approved_by=r[11],
                        approved_at=r[12],
                        completed_by=r[13],
                        completed_at=r[14],
                        confidence=r[15],
                        extraction_provenance=json.loads(r[16]),
                        version=r[17],
                        created_at=r[18],
                        updated_at=r[19],
                    )
                    for r in cur.fetchall()
                ]

                # Record deduplication audit event
                audit_id = f"aud_{uuid.uuid4().hex[:12]}"
                now_str = datetime.now(UTC).isoformat()
                cur.execute(
                    "INSERT INTO audit_events (event_id, workspace_id, entity_type, entity_id, action, "
                    "actor_type, actor_name, version_before, version_after, payload, created_at) "
                    "VALUES (?, ?, 'notice', ?, 'notice_deduplicated', 'system', 'Deduplicator', ?, ?, ?, ?)",
                    (
                        audit_id,
                        notice.workspace_id,
                        existing_notice.notice_id,
                        existing_notice.version,
                        existing_notice.version,
                        json.dumps(
                            {"fingerprint": notice.source_fingerprint, "title": notice.title}
                        ),
                        now_str,
                    ),
                )
                return existing_notice, existing_actions

            # 3. Capacity check (50 notices max per workspace)
            cur.execute(
                "SELECT COUNT(*) FROM notices WHERE workspace_id = ?",
                (notice.workspace_id,),
            )
            count_row = cur.fetchone()
            current_count = count_row[0] if count_row else 0
            if current_count >= 50:
                raise CapacityExceededError(
                    f"Workspace '{notice.workspace_id}' reached capacity limit of 50 notices.",
                    limit=50,
                    current=current_count,
                )

            # 4. Insert Notice
            now_str = datetime.now(UTC).isoformat()
            notice.created_at = now_str
            notice.updated_at = now_str
            cur.execute(
                "INSERT INTO notices (notice_id, workspace_id, source_type, class_name, child_alias, "
                "title, raw_body, raw_due_text, normalized_due_at, source_fingerprint, version, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    notice.notice_id,
                    notice.workspace_id,
                    notice.source_type,
                    notice.class_name,
                    notice.child_alias,
                    notice.title,
                    notice.raw_body,
                    notice.raw_due_text,
                    notice.normalized_due_at,
                    notice.source_fingerprint,
                    notice.version,
                    notice.created_at,
                    notice.updated_at,
                ),
            )

            # 5. Insert Actions
            for action in actions:
                action.created_at = now_str
                action.updated_at = now_str
                cur.execute(
                    "INSERT INTO actions (action_id, workspace_id, notice_id, action_type, title, "
                    "description, raw_deadline, normalized_deadline, amount_inr, status, "
                    "approval_required, approved_by, approved_at, completed_by, completed_at, "
                    "confidence, extraction_provenance, version, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        action.action_id,
                        action.workspace_id,
                        action.notice_id,
                        action.action_type,
                        action.title,
                        action.description,
                        action.raw_deadline,
                        action.normalized_deadline,
                        action.amount_inr,
                        action.status,
                        1 if action.approval_required else 0,
                        action.approved_by,
                        action.approved_at,
                        action.completed_by,
                        action.completed_at,
                        action.confidence,
                        json.dumps(action.extraction_provenance),
                        action.version,
                        action.created_at,
                        action.updated_at,
                    ),
                )

            # 6. Update workspace count
            cur.execute(
                "UPDATE workspaces SET notice_count = notice_count + 1, updated_at = ? WHERE workspace_id = ?",
                (now_str, notice.workspace_id),
            )

            # 7. Record audit event
            audit_id = f"aud_{uuid.uuid4().hex[:12]}"
            cur.execute(
                "INSERT INTO audit_events (event_id, workspace_id, entity_type, entity_id, action, "
                "actor_type, actor_name, version_before, version_after, payload, created_at) "
                "VALUES (?, ?, 'notice', ?, 'notice_created', 'parent', 'Parent Intake', 0, 1, ?, ?)",
                (
                    audit_id,
                    notice.workspace_id,
                    notice.notice_id,
                    json.dumps({"title": notice.title, "actions_extracted": len(actions)}),
                    now_str,
                ),
            )

            # 8. Store idempotency record if requested
            if idempotency_key and payload_hash:
                response_payload = {
                    "notice": notice.to_dict(),
                    "actions": [a.to_dict() for a in actions],
                }
                cur.execute(
                    "INSERT INTO idempotency_records (workspace_id, idempotency_key, payload_hash, status_code, response_body, created_at) "
                    "VALUES (?, ?, ?, 201, ?, ?)",
                    (
                        notice.workspace_id,
                        idempotency_key,
                        payload_hash,
                        json.dumps(response_payload),
                        now_str,
                    ),
                )

            return notice, actions

    def get_notice(self, workspace_id: str, notice_id: str) -> Notice | None:
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT notice_id, workspace_id, source_type, class_name, child_alias, title, "
                "raw_body, raw_due_text, normalized_due_at, source_fingerprint, version, created_at, updated_at "
                "FROM notices WHERE workspace_id = ? AND notice_id = ?",
                (workspace_id, notice_id),
            )
            r = cur.fetchone()
            if not r:
                return None
            return Notice(
                notice_id=r[0],
                workspace_id=r[1],
                source_type=r[2],
                class_name=r[3],
                child_alias=r[4],
                title=r[5],
                raw_body=r[6],
                raw_due_text=r[7],
                normalized_due_at=r[8],
                source_fingerprint=r[9],
                version=r[10],
                created_at=r[11],
                updated_at=r[12],
            )

    def find_notice_by_fingerprint(self, workspace_id: str, fingerprint: str) -> Notice | None:
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT notice_id, workspace_id, source_type, class_name, child_alias, title, "
                "raw_body, raw_due_text, normalized_due_at, source_fingerprint, version, created_at, updated_at "
                "FROM notices WHERE workspace_id = ? AND source_fingerprint = ?",
                (workspace_id, fingerprint),
            )
            r = cur.fetchone()
            if not r:
                return None
            return Notice(
                notice_id=r[0],
                workspace_id=r[1],
                source_type=r[2],
                class_name=r[3],
                child_alias=r[4],
                title=r[5],
                raw_body=r[6],
                raw_due_text=r[7],
                normalized_due_at=r[8],
                source_fingerprint=r[9],
                version=r[10],
                created_at=r[11],
                updated_at=r[12],
            )

    def list_notices(
        self,
        workspace_id: str,
        class_name: str | None = None,
        child_alias: str | None = None,
        source_type: str | None = None,
    ) -> list[Notice]:
        query = (
            "SELECT notice_id, workspace_id, source_type, class_name, child_alias, title, "
            "raw_body, raw_due_text, normalized_due_at, source_fingerprint, version, created_at, updated_at "
            "FROM notices WHERE workspace_id = ?"
        )
        params: list[Any] = [workspace_id]
        if class_name:
            query += " AND class_name = ?"
            params.append(class_name)
        if child_alias:
            query += " AND child_alias = ?"
            params.append(child_alias)
        if source_type:
            query += " AND source_type = ?"
            params.append(source_type)
        query += " ORDER BY created_at DESC"

        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, tuple(params))
            return [
                Notice(
                    notice_id=r[0],
                    workspace_id=r[1],
                    source_type=r[2],
                    class_name=r[3],
                    child_alias=r[4],
                    title=r[5],
                    raw_body=r[6],
                    raw_due_text=r[7],
                    normalized_due_at=r[8],
                    source_fingerprint=r[9],
                    version=r[10],
                    created_at=r[11],
                    updated_at=r[12],
                )
                for r in cur.fetchall()
            ]

    def get_notice_aggregate(self, workspace_id: str, notice_id: str) -> NoticeAggregate | None:
        notice = self.get_notice(workspace_id, notice_id)
        if not notice:
            return None
        actions = self.list_actions(workspace_id, notice_id=notice_id)
        reminders = self.list_reminders(workspace_id, notice_id=notice_id)
        entity_ids = (
            [notice_id] + [a.action_id for a in actions] + [r.reminder_id for r in reminders]
        )
        audit = self.list_audit_events_for_entities(workspace_id, entity_ids)
        return NoticeAggregate(
            notice=notice,
            actions=actions,
            reminders=reminders,
            audit_events=audit,
        )

    def list_audit_events_for_entities(
        self,
        workspace_id: str,
        entity_ids: list[str],
    ) -> list[AuditEvent]:
        if not entity_ids:
            return []
        placeholders = ",".join("?" for _ in entity_ids)
        query = (
            f"SELECT event_id, workspace_id, entity_type, entity_id, action, actor_type, "
            f"actor_name, version_before, version_after, payload, created_at "
            f"FROM audit_events WHERE workspace_id = ? AND entity_id IN ({placeholders}) "
            f"ORDER BY created_at ASC"
        )
        params: list[Any] = [workspace_id, *entity_ids]
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, tuple(params))
            return [
                AuditEvent(
                    event_id=r[0],
                    workspace_id=r[1],
                    entity_type=r[2],
                    entity_id=r[3],
                    action=r[4],
                    actor_type=r[5],
                    actor_name=r[6],
                    version_before=r[7],
                    version_after=r[8],
                    payload=json.loads(r[9]),
                    created_at=r[10],
                )
                for r in cur.fetchall()
            ]

    def get_action(self, workspace_id: str, action_id: str) -> SchoolAction | None:
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT action_id, workspace_id, notice_id, action_type, title, description, "
                "raw_deadline, normalized_deadline, amount_inr, status, approval_required, "
                "approved_by, approved_at, completed_by, completed_at, confidence, "
                "extraction_provenance, version, created_at, updated_at "
                "FROM actions WHERE workspace_id = ? AND action_id = ?",
                (workspace_id, action_id),
            )
            r = cur.fetchone()
            if not r:
                return None
            return SchoolAction(
                action_id=r[0],
                workspace_id=r[1],
                notice_id=r[2],
                action_type=r[3],
                title=r[4],
                description=r[5],
                raw_deadline=r[6],
                normalized_deadline=r[7],
                amount_inr=r[8],
                status=r[9],
                approval_required=bool(r[10]),
                approved_by=r[11],
                approved_at=r[12],
                completed_by=r[13],
                completed_at=r[14],
                confidence=r[15],
                extraction_provenance=json.loads(r[16]),
                version=r[17],
                created_at=r[18],
                updated_at=r[19],
            )

    def list_actions(
        self,
        workspace_id: str,
        notice_id: str | None = None,
        status: str | None = None,
    ) -> list[SchoolAction]:
        query = (
            "SELECT action_id, workspace_id, notice_id, action_type, title, description, "
            "raw_deadline, normalized_deadline, amount_inr, status, approval_required, "
            "approved_by, approved_at, completed_by, completed_at, confidence, "
            "extraction_provenance, version, created_at, updated_at "
            "FROM actions WHERE workspace_id = ?"
        )
        params: list[Any] = [workspace_id]
        if notice_id:
            query += " AND notice_id = ?"
            params.append(notice_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at ASC"

        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, tuple(params))
            return [
                SchoolAction(
                    action_id=r[0],
                    workspace_id=r[1],
                    notice_id=r[2],
                    action_type=r[3],
                    title=r[4],
                    description=r[5],
                    raw_deadline=r[6],
                    normalized_deadline=r[7],
                    amount_inr=r[8],
                    status=r[9],
                    approval_required=bool(r[10]),
                    approved_by=r[11],
                    approved_at=r[12],
                    completed_by=r[13],
                    completed_at=r[14],
                    confidence=r[15],
                    extraction_provenance=json.loads(r[16]),
                    version=r[17],
                    created_at=r[18],
                    updated_at=r[19],
                )
                for r in cur.fetchall()
            ]

    def update_action_deadline(
        self,
        workspace_id: str,
        action_id: str,
        expected_version: int,
        raw_deadline: str,
        normalized_deadline: str,
        actor_name: str = "Parent",
        idempotency_key: str | None = None,
        payload_hash: str | None = None,
    ) -> SchoolAction:
        """Edit action deadline with optimistic locking and audit logging."""
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()

            if idempotency_key:
                cur.execute(
                    "SELECT payload_hash, response_body FROM idempotency_records "
                    "WHERE workspace_id = ? AND idempotency_key = ?",
                    (workspace_id, idempotency_key),
                )
                idemp = cur.fetchone()
                if idemp:
                    if payload_hash and idemp[0] != payload_hash:
                        raise IdempotencyConflictError(idempotency_key)
                    return SchoolAction(**json.loads(idemp[1]))

            action = self.get_action(workspace_id, action_id)
            if not action:
                raise ActionNotFoundError(action_id)

            if action.version != expected_version:
                raise StateConflictError(action_id, action.version, expected_version)

            new_version = action.version + 1
            now_str = datetime.now(UTC).isoformat()

            cur.execute(
                "UPDATE actions SET raw_deadline = ?, normalized_deadline = ?, version = ?, updated_at = ? "
                "WHERE workspace_id = ? AND action_id = ? AND version = ?",
                (
                    raw_deadline,
                    normalized_deadline,
                    new_version,
                    now_str,
                    workspace_id,
                    action_id,
                    expected_version,
                ),
            )

            # Audit event
            audit_id = f"aud_{uuid.uuid4().hex[:12]}"
            cur.execute(
                "INSERT INTO audit_events (event_id, workspace_id, entity_type, entity_id, action, "
                "actor_type, actor_name, version_before, version_after, payload, created_at) "
                "VALUES (?, ?, 'action', ?, 'deadline_normalized', 'parent', ?, ?, ?, ?, ?)",
                (
                    audit_id,
                    workspace_id,
                    action_id,
                    actor_name,
                    expected_version,
                    new_version,
                    json.dumps(
                        {
                            "raw_deadline_before": action.raw_deadline,
                            "raw_deadline_after": raw_deadline,
                            "normalized_before": action.normalized_deadline,
                            "normalized_after": normalized_deadline,
                        }
                    ),
                    now_str,
                ),
            )

            action.raw_deadline = raw_deadline
            action.normalized_deadline = normalized_deadline
            action.version = new_version
            action.updated_at = now_str

            if idempotency_key and payload_hash:
                cur.execute(
                    "INSERT INTO idempotency_records (workspace_id, idempotency_key, payload_hash, status_code, response_body, created_at) "
                    "VALUES (?, ?, ?, 200, ?, ?)",
                    (
                        workspace_id,
                        idempotency_key,
                        payload_hash,
                        json.dumps(action.to_dict()),
                        now_str,
                    ),
                )

            return action

    def approve_action(
        self,
        workspace_id: str,
        action_id: str,
        expected_version: int,
        actor_type: str,
        actor_name: str,
        idempotency_key: str | None = None,
        payload_hash: str | None = None,
    ) -> SchoolAction:
        """Sign or approve action with strict human parent authority enforcement."""
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()

            if idempotency_key:
                cur.execute(
                    "SELECT payload_hash, response_body FROM idempotency_records "
                    "WHERE workspace_id = ? AND idempotency_key = ?",
                    (workspace_id, idempotency_key),
                )
                idemp = cur.fetchone()
                if idemp:
                    if payload_hash and idemp[0] != payload_hash:
                        raise IdempotencyConflictError(idempotency_key)
                    return SchoolAction(**json.loads(idemp[1]))

            action = self.get_action(workspace_id, action_id)
            if not action:
                raise ActionNotFoundError(action_id)

            # Strict Human Gate: only parent can approve if approval_required
            enforce_human_approval_gate(action, actor_type)

            if action.version != expected_version:
                raise StateConflictError(action_id, action.version, expected_version)

            validate_action_transition(action, ActionStatus.APPROVED.value)

            new_version = action.version + 1
            now_str = datetime.now(UTC).isoformat()

            cur.execute(
                "UPDATE actions SET status = 'approved', approved_by = ?, approved_at = ?, version = ?, updated_at = ? "
                "WHERE workspace_id = ? AND action_id = ? AND version = ?",
                (
                    actor_name,
                    now_str,
                    new_version,
                    now_str,
                    workspace_id,
                    action_id,
                    expected_version,
                ),
            )

            audit_id = f"aud_{uuid.uuid4().hex[:12]}"
            cur.execute(
                "INSERT INTO audit_events (event_id, workspace_id, entity_type, entity_id, action, "
                "actor_type, actor_name, version_before, version_after, payload, created_at) "
                "VALUES (?, ?, 'action', ?, 'action_approved', ?, ?, ?, ?, ?, ?)",
                (
                    audit_id,
                    workspace_id,
                    action_id,
                    actor_type,
                    actor_name,
                    expected_version,
                    new_version,
                    json.dumps(
                        {
                            "action_type": action.action_type,
                            "amount_inr": action.amount_inr,
                            "approved_by": actor_name,
                        }
                    ),
                    now_str,
                ),
            )

            action.status = ActionStatus.APPROVED.value
            action.approved_by = actor_name
            action.approved_at = now_str
            action.version = new_version
            action.updated_at = now_str

            if idempotency_key and payload_hash:
                cur.execute(
                    "INSERT INTO idempotency_records (workspace_id, idempotency_key, payload_hash, status_code, response_body, created_at) "
                    "VALUES (?, ?, ?, 200, ?, ?)",
                    (
                        workspace_id,
                        idempotency_key,
                        payload_hash,
                        json.dumps(action.to_dict()),
                        now_str,
                    ),
                )

            return action

    def complete_action(
        self,
        workspace_id: str,
        action_id: str,
        expected_version: int,
        actor_type: str,
        actor_name: str,
        idempotency_key: str | None = None,
        payload_hash: str | None = None,
    ) -> SchoolAction:
        """Mark action as completed by parent."""
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()

            if idempotency_key:
                cur.execute(
                    "SELECT payload_hash, response_body FROM idempotency_records "
                    "WHERE workspace_id = ? AND idempotency_key = ?",
                    (workspace_id, idempotency_key),
                )
                idemp = cur.fetchone()
                if idemp:
                    if payload_hash and idemp[0] != payload_hash:
                        raise IdempotencyConflictError(idempotency_key)
                    return SchoolAction(**json.loads(idemp[1]))

            action = self.get_action(workspace_id, action_id)
            if not action:
                raise ActionNotFoundError(action_id)

            if action.version != expected_version:
                raise StateConflictError(action_id, action.version, expected_version)

            validate_action_transition(action, ActionStatus.COMPLETED.value)

            new_version = action.version + 1
            now_str = datetime.now(UTC).isoformat()

            cur.execute(
                "UPDATE actions SET status = 'completed', completed_by = ?, completed_at = ?, version = ?, updated_at = ? "
                "WHERE workspace_id = ? AND action_id = ? AND version = ?",
                (
                    actor_name,
                    now_str,
                    new_version,
                    now_str,
                    workspace_id,
                    action_id,
                    expected_version,
                ),
            )

            audit_id = f"aud_{uuid.uuid4().hex[:12]}"
            cur.execute(
                "INSERT INTO audit_events (event_id, workspace_id, entity_type, entity_id, action, "
                "actor_type, actor_name, version_before, version_after, payload, created_at) "
                "VALUES (?, ?, 'action', ?, 'action_completed', ?, ?, ?, ?, ?, ?)",
                (
                    audit_id,
                    workspace_id,
                    action_id,
                    actor_type,
                    actor_name,
                    expected_version,
                    new_version,
                    json.dumps({"action_type": action.action_type, "completed_by": actor_name}),
                    now_str,
                ),
            )

            action.status = ActionStatus.COMPLETED.value
            action.completed_by = actor_name
            action.completed_at = now_str
            action.version = new_version
            action.updated_at = now_str

            if idempotency_key and payload_hash:
                cur.execute(
                    "INSERT INTO idempotency_records (workspace_id, idempotency_key, payload_hash, status_code, response_body, created_at) "
                    "VALUES (?, ?, ?, 200, ?, ?)",
                    (
                        workspace_id,
                        idempotency_key,
                        payload_hash,
                        json.dumps(action.to_dict()),
                        now_str,
                    ),
                )

            return action

    def create_reminder_draft(
        self,
        reminder: ReminderDraft,
        expected_action_version: int,
        actor_name: str = "Parent",
        idempotency_key: str | None = None,
        payload_hash: str | None = None,
    ) -> ReminderDraft:
        """Create a reminder/calendar draft for an action."""
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()

            if idempotency_key:
                cur.execute(
                    "SELECT payload_hash, response_body FROM idempotency_records "
                    "WHERE workspace_id = ? AND idempotency_key = ?",
                    (reminder.workspace_id, idempotency_key),
                )
                idemp = cur.fetchone()
                if idemp:
                    if payload_hash and idemp[0] != payload_hash:
                        raise IdempotencyConflictError(idempotency_key)
                    return ReminderDraft(**json.loads(idemp[1]))

            action = self.get_action(reminder.workspace_id, reminder.action_id)
            if not action:
                raise ActionNotFoundError(reminder.action_id)

            if action.version != expected_action_version:
                raise StateConflictError(
                    reminder.action_id, action.version, expected_action_version
                )

            now_str = datetime.now(UTC).isoformat()
            reminder.created_at = now_str
            reminder.updated_at = now_str

            cur.execute(
                "INSERT INTO reminder_drafts (reminder_id, workspace_id, action_id, notice_id, "
                "title, channel, scheduled_for, message_body, is_draft, version, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)",
                (
                    reminder.reminder_id,
                    reminder.workspace_id,
                    reminder.action_id,
                    reminder.notice_id,
                    reminder.title,
                    reminder.channel,
                    reminder.scheduled_for,
                    reminder.message_body,
                    reminder.version,
                    reminder.created_at,
                    reminder.updated_at,
                ),
            )

            audit_id = f"aud_{uuid.uuid4().hex[:12]}"
            cur.execute(
                "INSERT INTO audit_events (event_id, workspace_id, entity_type, entity_id, action, "
                "actor_type, actor_name, version_before, version_after, payload, created_at) "
                "VALUES (?, ?, 'reminder', ?, 'reminder_draft_created', 'parent', ?, 0, 1, ?, ?)",
                (
                    audit_id,
                    reminder.workspace_id,
                    reminder.reminder_id,
                    actor_name,
                    json.dumps(
                        {"channel": reminder.channel, "scheduled_for": reminder.scheduled_for}
                    ),
                    now_str,
                ),
            )

            if idempotency_key and payload_hash:
                cur.execute(
                    "INSERT INTO idempotency_records (workspace_id, idempotency_key, payload_hash, status_code, response_body, created_at) "
                    "VALUES (?, ?, ?, 201, ?, ?)",
                    (
                        reminder.workspace_id,
                        idempotency_key,
                        payload_hash,
                        json.dumps(reminder.to_dict()),
                        now_str,
                    ),
                )

            return reminder

    def list_reminders(
        self,
        workspace_id: str,
        action_id: str | None = None,
        notice_id: str | None = None,
    ) -> list[ReminderDraft]:
        query = (
            "SELECT reminder_id, workspace_id, action_id, notice_id, title, channel, "
            "scheduled_for, message_body, is_draft, version, created_at, updated_at "
            "FROM reminder_drafts WHERE workspace_id = ?"
        )
        params: list[Any] = [workspace_id]
        if action_id:
            query += " AND action_id = ?"
            params.append(action_id)
        if notice_id:
            query += " AND notice_id = ?"
            params.append(notice_id)
        query += " ORDER BY created_at ASC"

        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, tuple(params))
            return [
                ReminderDraft(
                    reminder_id=r[0],
                    workspace_id=r[1],
                    action_id=r[2],
                    notice_id=r[3],
                    title=r[4],
                    channel=r[5],
                    scheduled_for=r[6],
                    message_body=r[7],
                    is_draft=bool(r[8]),
                    version=r[9],
                    created_at=r[10],
                    updated_at=r[11],
                )
                for r in cur.fetchall()
            ]

    def record_audit_event(self, event: AuditEvent) -> None:
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO audit_events (event_id, workspace_id, entity_type, entity_id, action, "
                "actor_type, actor_name, version_before, version_after, payload, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event.event_id,
                    event.workspace_id,
                    event.entity_type,
                    event.entity_id,
                    event.action,
                    event.actor_type,
                    event.actor_name,
                    event.version_before,
                    event.version_after,
                    json.dumps(event.payload),
                    event.created_at,
                ),
            )

    def list_audit_events(
        self,
        workspace_id: str,
        entity_id: str | None = None,
    ) -> list[AuditEvent]:
        query = (
            "SELECT event_id, workspace_id, entity_type, entity_id, action, actor_type, "
            "actor_name, version_before, version_after, payload, created_at "
            "FROM audit_events WHERE workspace_id = ?"
        )
        params: list[Any] = [workspace_id]
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        query += " ORDER BY created_at ASC"

        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, tuple(params))
            return [
                AuditEvent(
                    event_id=r[0],
                    workspace_id=r[1],
                    entity_type=r[2],
                    entity_id=r[3],
                    action=r[4],
                    actor_type=r[5],
                    actor_name=r[6],
                    version_before=r[7],
                    version_after=r[8],
                    payload=json.loads(r[9]),
                    created_at=r[10],
                )
                for r in cur.fetchall()
            ]

    def get_idempotency_record(
        self, workspace_id: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT payload_hash, status_code, response_body, created_at "
                "FROM idempotency_records WHERE workspace_id = ? AND idempotency_key = ?",
                (workspace_id, idempotency_key),
            )
            r = cur.fetchone()
            if not r:
                return None
            return {
                "payload_hash": r[0],
                "status_code": r[1],
                "response_body": json.loads(r[2]),
                "created_at": r[3],
            }

    def save_idempotency_record(
        self,
        workspace_id: str,
        idempotency_key: str,
        payload_hash: str,
        status_code: int,
        response_body: dict[str, Any],
    ) -> None:
        now_str = datetime.now(UTC).isoformat()
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO idempotency_records (workspace_id, idempotency_key, payload_hash, status_code, response_body, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    workspace_id,
                    idempotency_key,
                    payload_hash,
                    status_code,
                    json.dumps(response_body),
                    now_str,
                ),
            )
