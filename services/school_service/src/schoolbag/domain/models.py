"""Domain models and value objects for Schoolbag."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class SourceType(StrEnum):
    WHATSAPP = "whatsapp"
    CIRCULAR_PDF = "circular_pdf"
    DIARY_NOTE = "diary_note"
    EMAIL = "email"
    SMS = "sms"


class ActionType(StrEnum):
    FEE_PAYMENT = "fee_payment"
    CONSENT_FORM = "consent_form"
    MATERIALS_BRING = "materials_bring"
    EXAM_PREP = "exam_prep"
    EVENT_ATTENDANCE = "event_attendance"


class ActionStatus(StrEnum):
    EXTRACTED = "extracted"
    DRAFT_READY = "draft_ready"
    APPROVED = "approved"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


class ActorType(StrEnum):
    PARENT = "parent"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ReminderChannel(StrEnum):
    CALENDAR = "calendar"
    SMS_DRAFT = "sms_draft"
    WHATSAPP_DRAFT = "whatsapp_draft"


@dataclass
class Notice:
    notice_id: str
    workspace_id: str
    source_type: str
    class_name: str
    child_alias: str
    title: str
    raw_body: str
    raw_due_text: str | None
    normalized_due_at: str | None
    source_fingerprint: str
    version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SchoolAction:
    action_id: str
    workspace_id: str
    notice_id: str
    action_type: str
    title: str
    description: str
    raw_deadline: str | None
    normalized_deadline: str | None
    amount_inr: float | None
    status: str
    approval_required: bool
    approved_by: str | None = None
    approved_at: str | None = None
    completed_by: str | None = None
    completed_at: str | None = None
    confidence: float = 1.0
    extraction_provenance: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReminderDraft:
    reminder_id: str
    workspace_id: str
    action_id: str
    notice_id: str
    title: str
    channel: str
    scheduled_for: str
    message_body: str
    is_draft: bool = True
    version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditEvent:
    event_id: str
    workspace_id: str
    entity_type: str
    entity_id: str
    action: str
    actor_type: str
    actor_name: str
    version_before: int
    version_after: int
    payload: dict[str, Any]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Workspace:
    workspace_id: str
    session_token: str
    notice_count: int = 0
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""
    expires_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NoticeAggregate:
    notice: Notice
    actions: list[SchoolAction] = field(default_factory=list)
    reminders: list[ReminderDraft] = field(default_factory=list)
    audit_events: list[AuditEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "notice": self.notice.to_dict(),
            "actions": [a.to_dict() for a in self.actions],
            "reminders": [r.to_dict() for r in self.reminders],
            "audit_events": [e.to_dict() for e in self.audit_events],
        }
