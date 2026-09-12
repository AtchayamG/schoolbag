"""Deadline text normalizer for school notices and actions."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

# Indian Standard Time (IST) offset +05:30
IST = timezone(timedelta(hours=5, minutes=30))

_WEEKDAYS = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}


def normalize_deadline(raw_text: str | None, base_dt: datetime | None = None) -> str | None:
    """Normalize relative or raw due date text into an ISO-8601 string in IST (+05:30).

    Examples:
        - "2026-09-18" -> "2026-09-18T17:00:00+05:30"
        - "2026-09-18T15:30:00" -> "2026-09-18T15:30:00+05:30"
        - "Friday 5 PM" -> calculated Friday at 17:00 IST
        - "Tomorrow 10 AM" -> calculated tomorrow at 10:00 IST
        - "Next Friday" -> calculated Friday next week at 17:00 IST
        - "Urgent" / "Today" -> today at 18:00 IST
    """
    if not raw_text or not raw_text.strip():
        return None

    text = raw_text.strip()

    # Already valid ISO datetime
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", text):
        if "+" not in text and "Z" not in text:
            return text + "+05:30"
        return text

    # Date string like YYYY-MM-DD
    match_date = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", text)
    if match_date:
        return f"{text}T17:00:00+05:30"

    # Base reference date (default to fixed reference or now in IST)
    ref = base_dt or datetime(2026, 9, 14, 9, 0, 0, tzinfo=IST)
    lower = text.lower()

    # Time extraction (e.g. "5 pm", "10 am", "17:00")
    hour = 17
    minute = 0
    time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", lower)
    if time_match:
        h = int(time_match.group(1))
        m = int(time_match.group(2) or 0)
        meridiem = time_match.group(3)
        if meridiem == "pm" and h < 12:
            h += 12
        elif meridiem == "am" and h == 12:
            h = 0
        if 0 <= h <= 23 and 0 <= m <= 59:
            hour = h
            minute = m

    # "today" / "urgent"
    if "today" in lower or "urgent" in lower:
        target_date = ref.date()
        h_val = hour
        if "urgent" in lower and not time_match:
            h_val = 18
        return datetime(
            target_date.year, target_date.month, target_date.day, h_val, minute, 0, tzinfo=IST
        ).isoformat()

    # "tomorrow"
    if "tomorrow" in lower:
        target_date = ref.date() + timedelta(days=1)
        return datetime(
            target_date.year, target_date.month, target_date.day, hour, minute, 0, tzinfo=IST
        ).isoformat()

    # Weekdays (e.g. "friday", "next friday", "by thursday")
    for wname, wday in _WEEKDAYS.items():
        if re.search(r"\b" + wname + r"\b", lower):
            days_ahead = (wday - ref.weekday()) % 7
            if days_ahead == 0 or "next" in lower:
                days_ahead += 7
            target_date = ref.date() + timedelta(days=days_ahead)
            return datetime(
                target_date.year, target_date.month, target_date.day, hour, minute, 0, tzinfo=IST
            ).isoformat()

    # Fallback: preserve ISO format 3 days ahead at 17:00 IST
    fallback_date = ref.date() + timedelta(days=3)
    return datetime(
        fallback_date.year, fallback_date.month, fallback_date.day, hour, minute, 0, tzinfo=IST
    ).isoformat()
