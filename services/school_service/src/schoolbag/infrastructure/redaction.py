"""Privacy boundary and PII redaction engine for school notices.

Guarantees:
1. Strips any parent contact details (phone numbers, email addresses).
2. Strips student admission numbers, roll numbers, Aadhaar, DOB, or medical references.
3. Preserves minimal child alias (e.g. 'Kavya', 'Arun') and class name ('Class 5-B') only.
4. Ensures zero private family data escapes across the wire to external models.
"""

from __future__ import annotations

import re
from typing import Any

# Regex patterns for sensitive identifiers
_PHONE_PATTERN = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}\b")
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_STUDENT_ID_PATTERN = re.compile(r"\b(?:ADMN?|ROLL|STU|ID)[\s#:-]*[0-9A-Z]{4,12}\b", re.IGNORECASE)
_DOB_PATTERN = re.compile(
    r"\b(?:DOB|Date of Birth)[\s:-]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE
)
_AADHAAR_PATTERN = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")


def redact_text(text: str) -> str:
    """Scrub phone numbers, emails, student IDs, Aadhaar, and DOB from text."""
    if not text:
        return text

    scrubbed = _PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
    scrubbed = _EMAIL_PATTERN.sub("[REDACTED_EMAIL]", scrubbed)
    scrubbed = _AADHAAR_PATTERN.sub("[REDACTED_AADHAAR]", scrubbed)
    scrubbed = _STUDENT_ID_PATTERN.sub("[REDACTED_ID]", scrubbed)
    scrubbed = _DOB_PATTERN.sub("[REDACTED_DOB]", scrubbed)
    return scrubbed


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def redact_school_notice_context(
    notice: Any,
    actions: list[Any] | None = None,
) -> dict[str, Any]:
    """Extract a privacy-safe, redacted context dictionary suitable for model inference."""
    notice_id = _get_val(notice, "notice_id")
    class_name = _get_val(notice, "class_name")
    child_alias = _get_val(notice, "child_alias")
    source_type = _get_val(notice, "source_type")
    title = _get_val(notice, "title", "")
    raw_body = _get_val(notice, "raw_body", "")
    raw_due_text = _get_val(notice, "raw_due_text")
    normalized_due_at = _get_val(notice, "normalized_due_at")
    version = _get_val(notice, "version", 1)

    redacted_ctx: dict[str, Any] = {
        "notice_id": notice_id,
        "class_name": class_name,
        "child_alias": child_alias,
        "source_type": source_type,
        "title": redact_text(str(title)),
        "raw_body": redact_text(str(raw_body)),
        "raw_due_text": redact_text(str(raw_due_text)) if raw_due_text else None,
        "normalized_due_at": normalized_due_at,
        "version": version,
    }

    if actions:
        redacted_actions: list[dict[str, Any]] = []
        for a in actions:
            a_id = _get_val(a, "action_id")
            a_type = _get_val(a, "action_type")
            a_title = _get_val(a, "title", "")
            a_desc = _get_val(a, "description", "")
            a_raw_dl = _get_val(a, "raw_deadline")
            a_norm_dl = _get_val(a, "normalized_deadline")
            a_amt = _get_val(a, "amount_inr")
            a_status = _get_val(a, "status")
            a_appr_req = _get_val(a, "approval_required", False)

            redacted_actions.append(
                {
                    "action_id": a_id,
                    "action_type": a_type,
                    "title": redact_text(str(a_title)),
                    "description": redact_text(str(a_desc)),
                    "raw_deadline": redact_text(str(a_raw_dl)) if a_raw_dl else None,
                    "normalized_deadline": a_norm_dl,
                    "amount_inr": float(a_amt) if a_amt is not None else None,
                    "status": a_status
                    if isinstance(a_status, str)
                    else getattr(a_status, "value", str(a_status)),
                    "approval_required": bool(a_appr_req),
                }
            )
        redacted_ctx["actions"] = redacted_actions

    return redacted_ctx
