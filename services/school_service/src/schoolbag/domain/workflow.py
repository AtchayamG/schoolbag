"""Workflow policies, state transitions, human authority gates, and hashing."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from schoolbag.domain.errors import (
    HumanApprovalRequiredError,
    InvalidStateTransitionError,
)
from schoolbag.domain.models import ActionStatus, ActorType, SchoolAction

_VALID_TRANSITIONS: dict[str, set[str]] = {
    ActionStatus.EXTRACTED.value: {
        ActionStatus.DRAFT_READY.value,
        ActionStatus.APPROVED.value,
        ActionStatus.DISMISSED.value,
    },
    ActionStatus.DRAFT_READY.value: {
        ActionStatus.APPROVED.value,
        ActionStatus.DISMISSED.value,
    },
    ActionStatus.APPROVED.value: {
        ActionStatus.COMPLETED.value,
        ActionStatus.DISMISSED.value,
    },
    ActionStatus.COMPLETED.value: set(),
    ActionStatus.DISMISSED.value: set(),
}


def validate_action_transition(action: SchoolAction, target_status: str) -> None:
    """Validate that action can transition from current status to target status."""
    allowed = _VALID_TRANSITIONS.get(action.status, set())
    if target_status not in allowed:
        raise InvalidStateTransitionError(
            action_id=action.action_id,
            current_status=action.status,
            target_status=target_status,
        )


def enforce_human_approval_gate(action: SchoolAction, actor_type: str) -> None:
    """Enforce that actions requiring approval strictly reject non-parent actors with 403."""
    if action.approval_required and actor_type.lower() != ActorType.PARENT.value:
        raise HumanApprovalRequiredError(
            action_id=action.action_id,
            action_type=action.action_type,
            actor_type=actor_type,
        )


def compute_notice_fingerprint(
    title: str,
    raw_body: str,
    source_type: str,
    class_name: str,
    child_alias: str,
) -> str:
    """Compute deterministic SHA-256 fingerprint for notice deduplication.

    Normalizes whitespace and lowercases to detect repeated forwards and notices.
    """
    clean_title = re.sub(r"\s+", " ", title.strip().lower())
    clean_body = re.sub(r"\s+", " ", raw_body.strip().lower())
    clean_class = class_name.strip().lower()
    clean_child = child_alias.strip().lower()
    clean_source = source_type.strip().lower()

    raw_key = f"{clean_source}:{clean_class}:{clean_child}:{clean_title}:{clean_body}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def canonical_payload_hash(payload: dict[str, Any]) -> str:
    """Compute SHA-256 hash of JSON payload excluding idempotency_key for replay detection."""
    filtered = {k: v for k, v in payload.items() if k != "idempotency_key"}
    canonical_json = json.dumps(filtered, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
