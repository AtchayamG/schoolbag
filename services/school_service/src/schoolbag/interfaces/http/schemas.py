"""Pydantic schemas for Schoolbag REST API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class CreateNoticeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str = Field(
        ..., description="Source medium: whatsapp, circular_pdf, diary_note, email, sms"
    )
    class_name: str = Field(..., description="Class identifier, e.g. Class 5-B")
    child_alias: str = Field(..., description="Privacy-preserving child alias, e.g. Kavya")
    title: str = Field(..., description="Notice subject or circular title")
    raw_body: str = Field(..., description="Raw text of the school message")
    raw_due_text: str | None = Field(None, description="Due date text as written in notice")
    idempotency_key: str | None = Field(None, description="Optional idempotency key")


class UpdateDeadlineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(..., description="Optimistic locking version")
    raw_deadline: str = Field(..., description="Updated deadline text")
    actor_name: str = Field(default="Parent", description="Actor performing the edit")
    idempotency_key: str | None = Field(None, description="Optional idempotency key")


class ApproveActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(..., description="Optimistic locking version")
    actor_type: str = Field(default="parent", description="Actor type: parent or assistant")
    actor_name: str = Field(default="Parent", description="Name/role of human parent")
    idempotency_key: str | None = Field(None, description="Optional idempotency key")


class CompleteActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(..., description="Optimistic locking version")
    actor_type: str = Field(default="parent", description="Actor type: parent")
    actor_name: str = Field(default="Parent", description="Name/role of parent signing completion")
    idempotency_key: str | None = Field(None, description="Optional idempotency key")


class CreateReminderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_action_version: int = Field(..., description="Action version when draft is requested")
    channel: str = Field(default="calendar", description="calendar, sms_draft, or whatsapp_draft")
    scheduled_for: str = Field(..., description="Target ISO datetime for reminder")
    message_body: str = Field(..., description="Draft message text or calendar entry note")
    actor_name: str = Field(default="Parent", description="Actor creating the draft")
    idempotency_key: str | None = Field(None, description="Optional idempotency key")


class ActionResponse(BaseModel):
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
    confidence: float
    extraction_provenance: dict[str, Any]
    version: int
    created_at: str
    updated_at: str


class NoticeResponse(BaseModel):
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
    version: int
    created_at: str
    updated_at: str


class ReminderResponse(BaseModel):
    reminder_id: str
    workspace_id: str
    action_id: str
    notice_id: str
    title: str
    channel: str
    scheduled_for: str
    message_body: str
    is_draft: bool
    version: int
    created_at: str
    updated_at: str


class AuditEventResponse(BaseModel):
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


class WorkspaceResponse(BaseModel):
    workspace_id: str
    session_token: str
    notice_count: int
    capacity_limit: int = 50
    is_active: bool
    created_at: str
    updated_at: str
    expires_at: str


class NoticeAggregateResponse(BaseModel):
    notice: NoticeResponse
    actions: list[ActionResponse]
    reminders: list[ReminderResponse]
    audit_events: list[AuditEventResponse]


class NoticeCreatedResponse(BaseModel):
    notice: NoticeResponse
    actions: list[ActionResponse]
    is_deduplicated: bool = False


class StrandsAdvisoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(..., description="Expected notice version for optimistic locking")
    idempotency_key: str | None = Field(None, description="Optional idempotency key")


class SuggestedActionSchema(BaseModel):
    category: str
    title: str
    description: str
    deadline_hint: str | None = None
    amount_inr: float | None = None
    approval_required: bool = False


class StrandsAdvisoryResponseSchema(BaseModel):
    notice_id: str
    source_version: int
    summary: str
    suggested_actions: list[SuggestedActionSchema]
    is_urgent: bool
    advisory_notes: str
    provenance: dict[str, Any]
