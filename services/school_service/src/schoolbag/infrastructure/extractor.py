"""Deterministic action extractor for school notices with truthful provenance."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Any

from schoolbag.domain.errors import (
    ExtractorInvalidOutputError,
    ExtractorUnavailableError,
)
from schoolbag.domain.models import ActionStatus, ActionType
from schoolbag.infrastructure.normalizer import normalize_deadline


class DeterministicActionExtractor:
    """Offline rule-based extractor for school notice actions with domain intelligence."""

    def __init__(self, mode: str = "deterministic") -> None:
        self.mode = mode

    def extract_actions(
        self,
        title: str,
        raw_body: str,
        raw_due_text: str | None,
        child_alias: str,
        class_name: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Extract structured actions from a notice with truthful provenance disclosure."""
        if self.mode == "unavailable":
            raise ExtractorUnavailableError("School extraction provider is offline or unreachable.")
        if self.mode == "invalid_output":
            raise ExtractorInvalidOutputError(
                "Extractor produced unparseable or corrupted action JSON."
            )

        now_iso = datetime.now(UTC).isoformat()
        full_text = f"{title}\n{raw_body}"
        lower = full_text.lower()
        extracted: list[dict[str, Any]] = []

        # 1. Fee Payment Check
        # Match currency e.g. Rs. 150, Rs 150, ₹150, 150 INR, 150 rupees
        fee_match = re.search(
            r"(?:rs\.?|₹|inr)\s*(\d+(?:\.\d{2})?)|(\d+)\s*(?:rs|rupees|inr)", lower
        )
        has_fee_words = any(
            w in lower for w in ["fee", "payment", "pay", "charges", "kit cost", "amount"]
        )
        if fee_match and has_fee_words:
            raw_amt = fee_match.group(1) or fee_match.group(2)
            amount = float(raw_amt) if raw_amt else None
            deadline_text = raw_due_text or "Friday 5 PM"
            extracted.append(
                {
                    "action_id": f"act_{uuid.uuid4().hex[:12]}",
                    "action_type": ActionType.FEE_PAYMENT.value,
                    "title": f"Pay {title.strip()} Fee (₹{int(amount) if amount else 0})",
                    "description": (
                        f"Submit fee payment of ₹{amount} for {child_alias} ({class_name}) "
                        f"as requested in notice."
                    ),
                    "raw_deadline": deadline_text,
                    "normalized_deadline": normalize_deadline(deadline_text),
                    "amount_inr": amount,
                    "status": ActionStatus.EXTRACTED.value,
                    "approval_required": True,  # Financial action strictly requires parent approval
                    "confidence": 0.96,
                }
            )

        # 2. Consent Form Check
        has_consent = any(
            w in lower
            for w in [
                "consent",
                "permission",
                "signed slip",
                "parent signature",
                "participation slip",
            ]
        )
        if has_consent:
            deadline_text = raw_due_text or "Thursday 4 PM"
            extracted.append(
                {
                    "action_id": f"act_{uuid.uuid4().hex[:12]}",
                    "action_type": ActionType.CONSENT_FORM.value,
                    "title": f"Sign Consent Form for {title.strip()}",
                    "description": (
                        f"Review and sign permission slip authorizing {child_alias}'s "
                        f"participation. Parent signature required."
                    ),
                    "raw_deadline": deadline_text,
                    "normalized_deadline": normalize_deadline(deadline_text),
                    "amount_inr": None,
                    "status": ActionStatus.EXTRACTED.value,
                    "approval_required": True,  # Legal / parental consent strictly requires parent approval
                    "confidence": 0.94,
                }
            )

        # 3. Materials to Bring Check
        has_materials = any(
            w in lower
            for w in [
                "bring",
                "materials",
                "chart paper",
                "sketch pen",
                "kit",
                "costume",
                "scissors",
                "craft",
                "supplies",
            ]
        )
        if has_materials:
            deadline_text = raw_due_text or "Tomorrow 9 AM"
            extracted.append(
                {
                    "action_id": f"act_{uuid.uuid4().hex[:12]}",
                    "action_type": ActionType.MATERIALS_BRING.value,
                    "title": f"Pack Required Materials for {class_name}",
                    "description": (
                        f"Prepare and pack requested supplies/materials in {child_alias}'s bag "
                        f"for class activity."
                    ),
                    "raw_deadline": deadline_text,
                    "normalized_deadline": normalize_deadline(deadline_text),
                    "amount_inr": None,
                    "status": ActionStatus.EXTRACTED.value,
                    "approval_required": False,  # Non-financial preparation task
                    "confidence": 0.91,
                }
            )

        # 4. Exam / Test Prep Check
        has_exam = any(
            w in lower
            for w in ["exam", "test", "syllabus", "revision", "hall ticket", "assessment"]
        )
        if has_exam and not any(a["action_type"] == ActionType.EXAM_PREP.value for a in extracted):
            deadline_text = raw_due_text or "Next Monday 9 AM"
            extracted.append(
                {
                    "action_id": f"act_{uuid.uuid4().hex[:12]}",
                    "action_type": ActionType.EXAM_PREP.value,
                    "title": f"Prepare for Assessment ({class_name})",
                    "description": f"Review syllabus and verify study materials for {child_alias}.",
                    "raw_deadline": deadline_text,
                    "normalized_deadline": normalize_deadline(deadline_text),
                    "amount_inr": None,
                    "status": ActionStatus.EXTRACTED.value,
                    "approval_required": False,
                    "confidence": 0.89,
                }
            )

        # 5. Fallback if fewer than 2 actions extracted: provide structured general action
        if len(extracted) < 2:
            deadline_text = raw_due_text or "Friday 5 PM"
            extracted.append(
                {
                    "action_id": f"act_{uuid.uuid4().hex[:12]}",
                    "action_type": ActionType.EVENT_ATTENDANCE.value,
                    "title": f"Acknowledge Notice: {title.strip()}",
                    "description": f"Read school circular for {child_alias} ({class_name}) and note instructions.",
                    "raw_deadline": deadline_text,
                    "normalized_deadline": normalize_deadline(deadline_text),
                    "amount_inr": None,
                    "status": ActionStatus.EXTRACTED.value,
                    "approval_required": False,
                    "confidence": 0.85,
                }
            )

        provenance = {
            "engine": "deterministic",
            "provider": "synthetic",
            "model": "grounded_rule_extractor",
            "extracted_at": now_iso,
            "actions_count": len(extracted),
            "advisory_only": True,
            "requires_parent_approval": any(a["approval_required"] for a in extracted),
        }

        return extracted, provenance
