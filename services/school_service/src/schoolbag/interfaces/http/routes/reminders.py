"""Calendar and reminder drafts routes and audit trail retrieval."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, Request, status

from schoolbag.domain.errors import ActionNotFoundError, ValidationError
from schoolbag.domain.models import ReminderDraft, Workspace
from schoolbag.domain.ports import SchoolbagStorePort
from schoolbag.domain.workflow import canonical_payload_hash
from schoolbag.interfaces.http.routes.session import get_current_workspace
from schoolbag.interfaces.http.schemas import (
    AuditEventResponse,
    CreateReminderRequest,
    ReminderResponse,
)

router = APIRouter(tags=["Reminders & Audit"])


def _resolve_idempotency_key(
    header_key: str | None,
    body_key: str | None,
) -> str | None:
    if header_key and body_key and header_key.strip() != body_key.strip():
        raise ValidationError(
            "Idempotency-Key header does not match body idempotency_key.",
            details={"header": header_key, "body": body_key},
        )
    return header_key.strip() if header_key else (body_key.strip() if body_key else None)


@router.post(
    "/api/actions/{action_id}/reminders",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reminder_draft(
    action_id: str,
    req: CreateReminderRequest,
    request: Request,
    idempotency_header: str | None = Header(None, alias="Idempotency-Key"),
    ws: Workspace = Depends(get_current_workspace),
) -> ReminderResponse:
    """Create a draft reminder / calendar item for an action."""
    store: SchoolbagStorePort = request.app.state.store
    idempotency_key = _resolve_idempotency_key(idempotency_header, req.idempotency_key)
    payload_dict = req.model_dump()
    payload_hash = canonical_payload_hash(payload_dict) if idempotency_key else None

    action = store.get_action(ws.workspace_id, action_id)
    if not action:
        raise ActionNotFoundError(action_id)

    reminder = ReminderDraft(
        reminder_id=f"rem_{uuid.uuid4().hex[:12]}",
        workspace_id=ws.workspace_id,
        action_id=action.action_id,
        notice_id=action.notice_id,
        title=f"Draft Reminder: {action.title}",
        channel=req.channel,
        scheduled_for=req.scheduled_for,
        message_body=req.message_body,
        is_draft=True,
        version=1,
    )

    created = store.create_reminder_draft(
        reminder=reminder,
        expected_action_version=req.expected_action_version,
        actor_name=req.actor_name,
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
    )
    return ReminderResponse(**created.to_dict())


@router.get("/api/reminders", response_model=list[ReminderResponse])
def list_reminders(
    action_id: str | None = None,
    notice_id: str | None = None,
    request: Request = None,  # type: ignore[assignment]
    ws: Workspace = Depends(get_current_workspace),
) -> list[ReminderResponse]:
    """List reminder and calendar drafts in current workspace."""
    store: SchoolbagStorePort = request.app.state.store
    reminders = store.list_reminders(ws.workspace_id, action_id=action_id, notice_id=notice_id)
    return [ReminderResponse(**r.to_dict()) for r in reminders]


@router.get("/api/audit", response_model=list[AuditEventResponse])
def list_audit_events(
    entity_id: str | None = None,
    request: Request = None,  # type: ignore[assignment]
    ws: Workspace = Depends(get_current_workspace),
) -> list[AuditEventResponse]:
    """Retrieve immutable audit event trail for actions and notices."""
    store: SchoolbagStorePort = request.app.state.store
    events = store.list_audit_events(ws.workspace_id, entity_id=entity_id)
    return [AuditEventResponse(**e.to_dict()) for e in events]
