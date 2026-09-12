"""Synthetic presets for Schoolbag with Tamil Nadu context."""

from __future__ import annotations

from typing import Any

PRESET_NOTICES: list[dict[str, Any]] = [
    {
        "preset_id": "preset-science-kit",
        "label": "Science Exhibition Kit & Supplies (WhatsApp)",
        "source_type": "whatsapp",
        "class_name": "Class 5-B",
        "child_alias": "Kavya",
        "title": "Science Exhibition Project Kit & Materials",
        "raw_body": (
            "Dear Parents of Class 5-B, for our upcoming Science Exhibition on Friday, "
            "each student must pay ₹150 towards the customized science experiment kit. "
            "Please also send 1 white chart paper, sketch pens, and safety craft scissors "
            "with your child by Thursday morning. — Mrs. Revathi (Class Teacher), "
            "Kovai Vidya Mandir, RS Puram, Coimbatore."
        ),
        "raw_due_text": "Friday 5 PM",
    },
    {
        "preset_id": "preset-annual-day",
        "label": "Annual Day Cultural Dance Consent (PDF Circular)",
        "source_type": "circular_pdf",
        "class_name": "Class 5-B",
        "child_alias": "Kavya",
        "title": "Annual Day Cultural Dance Participation",
        "raw_body": (
            "Circular No. KVM/2026/AD-14: We are pleased to announce rehearsals for the "
            "Annual Day Tamil Folk Dance. Students participating must submit the signed "
            "consent slip from their parent by Wednesday 4 PM. A nominal costume hire fee "
            "of ₹300 is applicable upon parent confirmation. — Dr. Meenakshi Sundaram, Principal."
        ),
        "raw_due_text": "Wednesday 4 PM",
    },
    {
        "preset_id": "preset-term-exam",
        "label": "Term Assessment & Geometry Kit (SMS)",
        "source_type": "sms",
        "class_name": "Class 8-A",
        "child_alias": "Arun",
        "title": "Term 1 Assessment Time-Table Released",
        "raw_body": (
            "School Alert: Term 1 assessment schedule has been published. Mathematics exam "
            "commences next Monday 9:30 AM. Ensure child brings complete geometry box, "
            "writing board, and verified hall ticket. — School Admin Office, Coimbatore."
        ),
        "raw_due_text": "Next Monday 9 AM",
    },
]


def get_preset_by_id(preset_id: str) -> dict[str, Any] | None:
    for preset in PRESET_NOTICES:
        if preset["preset_id"] == preset_id:
            return preset
    return None
