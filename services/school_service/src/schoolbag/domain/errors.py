"""Domain exception hierarchy for Schoolbag."""

from __future__ import annotations

from typing import Any


class SchoolbagDomainError(Exception):
    """Base domain exception for Schoolbag with status code and error code."""

    def __init__(
        self,
        message: str,
        code: str = "DOMAIN_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NoticeNotFoundError(SchoolbagDomainError):
    def __init__(self, notice_id: str) -> None:
        super().__init__(
            message=f"School notice '{notice_id}' was not found.",
            code="NOTICE_NOT_FOUND",
            status_code=404,
            details={"notice_id": notice_id},
        )


class ActionNotFoundError(SchoolbagDomainError):
    def __init__(self, action_id: str) -> None:
        super().__init__(
            message=f"Action '{action_id}' was not found.",
            code="ACTION_NOT_FOUND",
            status_code=404,
            details={"action_id": action_id},
        )


class ReminderNotFoundError(SchoolbagDomainError):
    def __init__(self, reminder_id: str) -> None:
        super().__init__(
            message=f"Reminder draft '{reminder_id}' was not found.",
            code="REMINDER_NOT_FOUND",
            status_code=404,
            details={"reminder_id": reminder_id},
        )


class HumanApprovalRequiredError(SchoolbagDomainError):
    """Raised when an assistant or automated actor attempts an action requiring parent authority."""

    def __init__(self, action_id: str, action_type: str, actor_type: str) -> None:
        super().__init__(
            message=(
                f"Action '{action_id}' ({action_type}) requires explicit human parent approval. "
                f"Actor '{actor_type}' is not authorized to sign consent or execute payment."
            ),
            code="HUMAN_APPROVAL_REQUIRED",
            status_code=403,
            details={
                "action_id": action_id,
                "action_type": action_type,
                "actor_type": actor_type,
                "required_actor": "parent",
            },
        )


class StateConflictError(SchoolbagDomainError):
    """Raised when optimistic concurrency check fails (version mismatch)."""

    def __init__(self, entity_id: str, current_version: int, expected_version: int) -> None:
        super().__init__(
            message=(
                f"Conflict on entity '{entity_id}'. Current version is {current_version}, "
                f"but expected version was {expected_version}."
            ),
            code="STATE_CONFLICT",
            status_code=409,
            details={
                "entity_id": entity_id,
                "current_version": current_version,
                "expected_version": expected_version,
            },
        )


class IdempotencyConflictError(SchoolbagDomainError):
    """Raised when an idempotency key is reused with a different request payload."""

    def __init__(self, idempotency_key: str) -> None:
        super().__init__(
            message=f"Idempotency key '{idempotency_key}' was previously used with a different request payload.",
            code="IDEMPOTENCY_CONFLICT",
            status_code=409,
            details={"idempotency_key": idempotency_key},
        )


class CapacityExceededError(SchoolbagDomainError):
    """Raised when workspace capacity (e.g. 50 notices) or global workspace limit is reached."""

    def __init__(self, message: str, limit: int, current: int) -> None:
        super().__init__(
            message=message,
            code="CAPACITY_EXCEEDED",
            status_code=409,
            details={"limit": limit, "current": current},
        )


class InvalidStateTransitionError(SchoolbagDomainError):
    """Raised when an invalid action status transition is attempted."""

    def __init__(self, action_id: str, current_status: str, target_status: str) -> None:
        super().__init__(
            message=f"Cannot transition action '{action_id}' from '{current_status}' to '{target_status}'.",
            code="INVALID_STATE_TRANSITION",
            status_code=400,
            details={
                "action_id": action_id,
                "current_status": current_status,
                "target_status": target_status,
            },
        )


class SessionExpiredError(SchoolbagDomainError):
    """Raised when workspace session is missing or expired in production."""

    def __init__(self, message: str = "Workbench session expired or invalid.") -> None:
        super().__init__(
            message=message,
            code="SESSION_EXPIRED",
            status_code=401,
        )


class OriginRefusedError(SchoolbagDomainError):
    """Raised when request Origin header is forbidden or missing in production."""

    def __init__(self, message: str = "Request origin refused by security policy.") -> None:
        super().__init__(
            message=message,
            code="ORIGIN_REFUSED",
            status_code=403,
        )


class ExtractorUnavailableError(SchoolbagDomainError):
    """Raised when extraction service is unavailable."""

    def __init__(self, message: str = "Extraction provider is temporarily unavailable.") -> None:
        super().__init__(
            message=message,
            code="EXTRACTOR_UNAVAILABLE",
            status_code=503,
        )


class ExtractorInvalidOutputError(SchoolbagDomainError):
    """Raised when extraction output cannot be parsed or grounded."""

    def __init__(self, message: str = "Extraction output was malformed or ungrounded.") -> None:
        super().__init__(
            message=message,
            code="EXTRACTOR_INVALID_OUTPUT",
            status_code=502,
        )


class ValidationError(SchoolbagDomainError):
    """Raised when domain validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details or {},
        )
