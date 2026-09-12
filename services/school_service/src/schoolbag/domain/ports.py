"""Port abstractions for store and action extraction."""

from __future__ import annotations

from typing import Any, Protocol

from schoolbag.domain.models import (
    AuditEvent,
    Notice,
    NoticeAggregate,
    ReminderDraft,
    SchoolAction,
    Workspace,
)


class SchoolbagStorePort(Protocol):
    """Protocol defining storage operations for notices, actions, and audit logs."""

    def get_or_create_workspace(self, session_token: str) -> Workspace: ...

    def get_workspace_by_id(self, workspace_id: str) -> Workspace | None: ...

    def create_notice(
        self,
        notice: Notice,
        actions: list[SchoolAction],
        idempotency_key: str | None = None,
        payload_hash: str | None = None,
    ) -> tuple[Notice, list[SchoolAction]]: ...

    def get_notice(self, workspace_id: str, notice_id: str) -> Notice | None: ...

    def find_notice_by_fingerprint(self, workspace_id: str, fingerprint: str) -> Notice | None: ...

    def list_notices(
        self,
        workspace_id: str,
        class_name: str | None = None,
        child_alias: str | None = None,
        source_type: str | None = None,
    ) -> list[Notice]: ...

    def get_notice_aggregate(self, workspace_id: str, notice_id: str) -> NoticeAggregate | None: ...

    def get_action(self, workspace_id: str, action_id: str) -> SchoolAction | None: ...

    def list_actions(
        self,
        workspace_id: str,
        notice_id: str | None = None,
        status: str | None = None,
    ) -> list[SchoolAction]: ...

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
    ) -> SchoolAction: ...

    def approve_action(
        self,
        workspace_id: str,
        action_id: str,
        expected_version: int,
        actor_type: str,
        actor_name: str,
        idempotency_key: str | None = None,
        payload_hash: str | None = None,
    ) -> SchoolAction: ...

    def complete_action(
        self,
        workspace_id: str,
        action_id: str,
        expected_version: int,
        actor_type: str,
        actor_name: str,
        idempotency_key: str | None = None,
        payload_hash: str | None = None,
    ) -> SchoolAction: ...

    def create_reminder_draft(
        self,
        reminder: ReminderDraft,
        expected_action_version: int,
        actor_name: str = "Parent",
        idempotency_key: str | None = None,
        payload_hash: str | None = None,
    ) -> ReminderDraft: ...

    def list_reminders(
        self,
        workspace_id: str,
        action_id: str | None = None,
        notice_id: str | None = None,
    ) -> list[ReminderDraft]: ...

    def record_audit_event(self, event: AuditEvent) -> None: ...

    def list_audit_events(
        self,
        workspace_id: str,
        entity_id: str | None = None,
    ) -> list[AuditEvent]: ...

    def get_idempotency_record(
        self, workspace_id: str, idempotency_key: str
    ) -> dict[str, Any] | None: ...

    def save_idempotency_record(
        self,
        workspace_id: str,
        idempotency_key: str,
        payload_hash: str,
        status_code: int,
        response_body: dict[str, Any],
    ) -> None: ...


class ActionExtractorPort(Protocol):
    """Protocol for extracting structured school actions from notice text."""

    def extract_actions(
        self,
        title: str,
        raw_body: str,
        raw_due_text: str | None,
        child_alias: str,
        class_name: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]: ...
