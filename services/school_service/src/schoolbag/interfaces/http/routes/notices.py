"""School notice intake, listing, deduplication, and presets."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Request, status

from schoolbag.domain.errors import NoticeNotFoundError, ValidationError
from schoolbag.domain.models import Notice, SchoolAction, Workspace
from schoolbag.domain.ports import ActionExtractorPort, SchoolbagStorePort
from schoolbag.domain.workflow import (
    canonical_payload_hash,
    compute_notice_fingerprint,
)
from schoolbag.infrastructure.normalizer import normalize_deadline
from schoolbag.infrastructure.seed_data import PRESET_NOTICES
from schoolbag.interfaces.http.routes.session import get_current_workspace
from schoolbag.interfaces.http.schemas import (
    ActionResponse,
    AuditEventResponse,
    CreateNoticeRequest,
    NoticeAggregateResponse,
    NoticeCreatedResponse,
    NoticeResponse,
    ReminderResponse,
)

router = APIRouter(tags=["Notices"])


def _resolve_idempotency_key(
    header_key: str | None,
    body_key: str | None,
) -> str | None:
    """Ensure agreement between Idempotency-Key header and body payload."""
    if header_key and body_key and header_key.strip() != body_key.strip():
        raise ValidationError(
            "Idempotency-Key header does not match body idempotency_key.",
            details={"header": header_key, "body": body_key},
        )
    return header_key.strip() if header_key else (body_key.strip() if body_key else None)


@router.post(
    "/api/notices", response_model=NoticeCreatedResponse, status_code=status.HTTP_201_CREATED
)
def intake_notice(
    req: CreateNoticeRequest,
    request: Request,
    idempotency_header: str | None = Header(None, alias="Idempotency-Key"),
    ws: Workspace = Depends(get_current_workspace),
) -> Any:
    """Intake school notice, extract action items, compute fingerprint, and deduplicate."""
    store: SchoolbagStorePort = request.app.state.store
    extractor: ActionExtractorPort = request.app.state.extractor

    idempotency_key = _resolve_idempotency_key(idempotency_header, req.idempotency_key)
    payload_dict = req.model_dump()
    payload_hash = canonical_payload_hash(payload_dict) if idempotency_key else None

    # Compute content fingerprint
    fingerprint = compute_notice_fingerprint(
        title=req.title,
        raw_body=req.raw_body,
        source_type=req.source_type,
        class_name=req.class_name,
        child_alias=req.child_alias,
    )

    # Check for existing duplicate notice
    existing_notice = store.find_notice_by_fingerprint(ws.workspace_id, fingerprint)
    if existing_notice:
        existing_actions = store.list_actions(ws.workspace_id, notice_id=existing_notice.notice_id)
        return NoticeCreatedResponse(
            notice=NoticeResponse(**existing_notice.to_dict()),
            actions=[ActionResponse(**a.to_dict()) for a in existing_actions],
            is_deduplicated=True,
        )

    # Extract actions via extractor
    raw_actions, provenance = extractor.extract_actions(
        title=req.title,
        raw_body=req.raw_body,
        raw_due_text=req.raw_due_text,
        child_alias=req.child_alias,
        class_name=req.class_name,
    )

    notice_id = f"not_{uuid.uuid4().hex[:12]}"
    normalized_due = normalize_deadline(req.raw_due_text)

    notice = Notice(
        notice_id=notice_id,
        workspace_id=ws.workspace_id,
        source_type=req.source_type,
        class_name=req.class_name,
        child_alias=req.child_alias,
        title=req.title,
        raw_body=req.raw_body,
        raw_due_text=req.raw_due_text,
        normalized_due_at=normalized_due,
        source_fingerprint=fingerprint,
        version=1,
    )

    actions = [
        SchoolAction(
            action_id=f"act_{uuid.uuid4().hex[:12]}",
            workspace_id=ws.workspace_id,
            notice_id=notice_id,
            action_type=a["action_type"],
            title=a["title"],
            description=a["description"],
            raw_deadline=a.get("raw_deadline"),
            normalized_deadline=a.get("normalized_deadline"),
            amount_inr=a.get("amount_inr"),
            status=a["status"],
            approval_required=a.get("approval_required", False),
            confidence=a.get("confidence", 1.0),
            extraction_provenance=provenance,
            version=1,
        )
        for a in raw_actions
    ]

    saved_notice, saved_actions = store.create_notice(
        notice=notice,
        actions=actions,
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
    )

    return NoticeCreatedResponse(
        notice=NoticeResponse(**saved_notice.to_dict()),
        actions=[ActionResponse(**a.to_dict()) for a in saved_actions],
        is_deduplicated=False,
    )


@router.get("/api/notices", response_model=list[NoticeResponse])
def list_notices(
    class_name: str | None = None,
    child_alias: str | None = None,
    source_type: str | None = None,
    request: Request = None,  # type: ignore[assignment]
    ws: Workspace = Depends(get_current_workspace),
) -> list[NoticeResponse]:
    """List all school notices in current workspace with optional filters."""
    store: SchoolbagStorePort = request.app.state.store
    notices = store.list_notices(
        workspace_id=ws.workspace_id,
        class_name=class_name,
        child_alias=child_alias,
        source_type=source_type,
    )
    return [NoticeResponse(**n.to_dict()) for n in notices]


@router.get("/api/notices/{notice_id}", response_model=NoticeAggregateResponse)
def get_notice_details(
    notice_id: str,
    request: Request,
    ws: Workspace = Depends(get_current_workspace),
) -> NoticeAggregateResponse:
    """Get full aggregate details for a notice including extracted actions, reminders, and audit trail."""
    store: SchoolbagStorePort = request.app.state.store
    aggregate = store.get_notice_aggregate(ws.workspace_id, notice_id)
    if not aggregate:
        raise NoticeNotFoundError(notice_id)
    return NoticeAggregateResponse(
        notice=NoticeResponse(**aggregate.notice.to_dict()),
        actions=[ActionResponse(**a.to_dict()) for a in aggregate.actions],
        reminders=[ReminderResponse(**r.to_dict()) for r in aggregate.reminders],
        audit_events=[AuditEventResponse(**e.to_dict()) for e in aggregate.audit_events],
    )


@router.get("/api/presets", response_model=list[dict[str, Any]])
def get_presets() -> list[dict[str, Any]]:
    """Return synthetic public school notice presets with Tamil Nadu context."""
    return PRESET_NOTICES
