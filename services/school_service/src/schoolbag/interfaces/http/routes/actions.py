"""School action management, deadline normalization, approval, and completion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request

from schoolbag.domain.errors import ActionNotFoundError, ValidationError
from schoolbag.domain.models import Workspace
from schoolbag.domain.ports import SchoolbagStorePort
from schoolbag.domain.workflow import canonical_payload_hash
from schoolbag.infrastructure.normalizer import normalize_deadline
from schoolbag.interfaces.http.routes.session import get_current_workspace
from schoolbag.interfaces.http.schemas import (
    ActionResponse,
    ApproveActionRequest,
    CompleteActionRequest,
    UpdateDeadlineRequest,
)

router = APIRouter(prefix="/api/actions", tags=["Actions"])


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


@router.get("", response_model=list[ActionResponse])
def list_actions(
    notice_id: str | None = None,
    status: str | None = None,
    request: Request = None,  # type: ignore[assignment]
    ws: Workspace = Depends(get_current_workspace),
) -> list[ActionResponse]:
    """List school actions in current workspace."""
    store: SchoolbagStorePort = request.app.state.store
    actions = store.list_actions(ws.workspace_id, notice_id=notice_id, status=status)
    return [ActionResponse(**a.to_dict()) for a in actions]


@router.get("/{action_id}", response_model=ActionResponse)
def get_action(
    action_id: str,
    request: Request,
    ws: Workspace = Depends(get_current_workspace),
) -> ActionResponse:
    """Retrieve single action by ID."""
    store: SchoolbagStorePort = request.app.state.store
    action = store.get_action(ws.workspace_id, action_id)
    if not action:
        raise ActionNotFoundError(action_id)
    return ActionResponse(**action.to_dict())


@router.patch("/{action_id}/deadline", response_model=ActionResponse)
def update_action_deadline(
    action_id: str,
    req: UpdateDeadlineRequest,
    request: Request,
    idempotency_header: str | None = Header(None, alias="Idempotency-Key"),
    ws: Workspace = Depends(get_current_workspace),
) -> ActionResponse:
    """Edit action deadline with normalization and audit logging."""
    store: SchoolbagStorePort = request.app.state.store
    idempotency_key = _resolve_idempotency_key(idempotency_header, req.idempotency_key)
    payload_dict = req.model_dump()
    payload_hash = canonical_payload_hash(payload_dict) if idempotency_key else None

    normalized = normalize_deadline(req.raw_deadline) or req.raw_deadline

    updated = store.update_action_deadline(
        workspace_id=ws.workspace_id,
        action_id=action_id,
        expected_version=req.expected_version,
        raw_deadline=req.raw_deadline,
        normalized_deadline=normalized,
        actor_name=req.actor_name,
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
    )
    return ActionResponse(**updated.to_dict())


@router.post("/{action_id}/approve", response_model=ActionResponse)
def approve_action(
    action_id: str,
    req: ApproveActionRequest,
    request: Request,
    idempotency_header: str | None = Header(None, alias="Idempotency-Key"),
    ws: Workspace = Depends(get_current_workspace),
) -> ActionResponse:
    """Authorize fee payment or sign consent with strict human approval enforcement."""
    store: SchoolbagStorePort = request.app.state.store
    idempotency_key = _resolve_idempotency_key(idempotency_header, req.idempotency_key)
    payload_dict = req.model_dump()
    payload_hash = canonical_payload_hash(payload_dict) if idempotency_key else None

    approved = store.approve_action(
        workspace_id=ws.workspace_id,
        action_id=action_id,
        expected_version=req.expected_version,
        actor_type=req.actor_type,
        actor_name=req.actor_name,
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
    )
    return ActionResponse(**approved.to_dict())


@router.post("/{action_id}/complete", response_model=ActionResponse)
def complete_action(
    action_id: str,
    req: CompleteActionRequest,
    request: Request,
    idempotency_header: str | None = Header(None, alias="Idempotency-Key"),
    ws: Workspace = Depends(get_current_workspace),
) -> ActionResponse:
    """Mark action as completed by parent."""
    store: SchoolbagStorePort = request.app.state.store
    idempotency_key = _resolve_idempotency_key(idempotency_header, req.idempotency_key)
    payload_dict = req.model_dump()
    payload_hash = canonical_payload_hash(payload_dict) if idempotency_key else None

    completed = store.complete_action(
        workspace_id=ws.workspace_id,
        action_id=action_id,
        expected_version=req.expected_version,
        actor_type=req.actor_type,
        actor_name=req.actor_name,
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
    )
    return ActionResponse(**completed.to_dict())
