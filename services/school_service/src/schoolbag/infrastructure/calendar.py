"""RFC 5545 iCalendar (.ics) Generator for Schoolbag Actions.

Converts normalized school actions and deadlines into compliant iCalendar event
streams suitable for importing into Google Calendar, Apple Calendar, or Outlook.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import Any


def _escape_ics_text(text: str | None) -> str:
    """Escape special characters according to RFC 5545."""
    if not text:
        return ""
    res = text.replace("\\", "\\\\")
    res = res.replace(";", "\\;")
    res = res.replace(",", "\\,")
    res = res.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    return res


def _parse_to_utc_ics(dt_str: str | None) -> tuple[str, str]:
    """Parse an ISO datetime string and return (DTSTART, DTEND) formatted in UTC as YYYYMMDDTHHMMSSZ.

    Defaults to 1-hour duration. If dt_str is missing or invalid, defaults to tomorrow 09:00 IST.
    """
    now_utc = datetime.now(UTC)
    if not dt_str:
        start_dt = (now_utc + timedelta(days=1)).replace(
            hour=3, minute=30, second=0, microsecond=0
        )  # 09:00 IST = 03:30 UTC
        end_dt = start_dt + timedelta(hours=1)
    else:
        try:
            parsed = datetime.fromisoformat(dt_str)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
            start_dt = parsed.astimezone(UTC)
            end_dt = start_dt + timedelta(hours=1)
        except Exception:
            start_dt = (now_utc + timedelta(days=1)).replace(
                hour=3, minute=30, second=0, microsecond=0
            )
            end_dt = start_dt + timedelta(hours=1)

    fmt = "%Y%m%dT%H%M%SZ"
    return start_dt.strftime(fmt), end_dt.strftime(fmt)


def generate_action_ics(
    action: Any,
    notice: Any | None = None,
) -> str:
    """Generate RFC 5545 iCalendar file string for a single SchoolAction."""
    action_id = getattr(action, "action_id", None) or getattr(action, "id", "act_unknown")
    title = getattr(action, "title", "School Obligation")
    category = getattr(action, "category", "general")
    status = getattr(action, "status", "draft")
    description = getattr(action, "description", "")
    amount_inr = getattr(action, "amount_inr", None)
    if amount_inr is None:
        amount_inr = getattr(action, "amount", None)
    deadline = getattr(action, "normalized_deadline", None) or getattr(
        action, "normalized_due_date", None
    )
    if not deadline:
        deadline = getattr(action, "raw_deadline", None) or getattr(action, "due_date", None)

    child_alias = ""
    class_name = ""
    if notice:
        child_alias = getattr(notice, "child_alias", "") or ""
        class_name = getattr(notice, "class_name", "") or ""

    summary_prefix = f"[{child_alias}] " if child_alias else ""
    summary = f"{summary_prefix}{title}"
    if class_name:
        summary += f" ({class_name})"

    desc_lines = [
        description,
        "",
        f"Category: {category.capitalize()}",
        f"Status: {status.capitalize()}",
    ]
    if amount_inr is not None:
        desc_lines.append(f"Amount: ₹{amount_inr} INR")
    desc_lines.append("")
    desc_lines.append("Notice: Schoolbag Advisory - Requires Explicit Human Parent Action.")

    full_desc = "\n".join(desc_lines)
    dt_start, dt_end = _parse_to_utc_ics(deadline)
    dt_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Agents For Humans//Schoolbag v0.3.0//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:action-{action_id}@schoolbag.internal",
        f"DTSTAMP:{dt_stamp}",
        f"DTSTART:{dt_start}",
        f"DTEND:{dt_end}",
        f"SUMMARY:{_escape_ics_text(summary)}",
        f"DESCRIPTION:{_escape_ics_text(full_desc)}",
        f"CATEGORIES:{_escape_ics_text(category.upper())}",
        "STATUS:CONFIRMED",
        "BEGIN:VALARM",
        "TRIGGER:-PT2H",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Reminder: {_escape_ics_text(summary)}",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
    return "\r\n".join(lines)


def generate_workspace_calendar_ics(
    actions: list[Any],
    notices_by_id: dict[str, Any] | None = None,
) -> str:
    """Generate an aggregate RFC 5545 iCalendar feed for all workspace actions."""
    dt_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    notices = notices_by_id or {}

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Agents For Humans//Schoolbag Workspace Feed v0.3.0//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Schoolbag Family Schedule",
        "X-WR-TIMEZONE:Asia/Kolkata",
    ]

    for action in actions:
        action_id = getattr(action, "action_id", None) or getattr(action, "id", "act_unknown")
        title = getattr(action, "title", "School Obligation")
        category = getattr(action, "category", "general")
        status = getattr(action, "status", "draft")
        description = getattr(action, "description", "")
        notice_id = getattr(action, "notice_id", "")
        notice = notices.get(notice_id)

        amount_inr = getattr(action, "amount_inr", None) or getattr(action, "amount", None)
        deadline = getattr(action, "normalized_deadline", None) or getattr(
            action, "normalized_due_date", None
        )
        if not deadline:
            deadline = getattr(action, "raw_deadline", None) or getattr(action, "due_date", None)

        child_alias = ""
        class_name = ""
        if notice:
            child_alias = getattr(notice, "child_alias", "") or ""
            class_name = getattr(notice, "class_name", "") or ""

        summary_prefix = f"[{child_alias}] " if child_alias else ""
        summary = f"{summary_prefix}{title}"
        if class_name:
            summary += f" ({class_name})"

        desc_lines = [
            description,
            "",
            f"Category: {category.capitalize()}",
            f"Status: {status.capitalize()}",
        ]
        if amount_inr is not None:
            desc_lines.append(f"Amount: ₹{amount_inr} INR")
        desc_lines.append("")
        desc_lines.append("Notice: Schoolbag Advisory - Requires Explicit Human Parent Action.")

        full_desc = "\n".join(desc_lines)
        dt_start, dt_end = _parse_to_utc_ics(deadline)

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:action-{action_id}@schoolbag.internal",
                f"DTSTAMP:{dt_stamp}",
                f"DTSTART:{dt_start}",
                f"DTEND:{dt_end}",
                f"SUMMARY:{_escape_ics_text(summary)}",
                f"DESCRIPTION:{_escape_ics_text(full_desc)}",
                f"CATEGORIES:{_escape_ics_text(category.upper())}",
                "STATUS:CONFIRMED",
                "BEGIN:VALARM",
                "TRIGGER:-PT2H",
                "ACTION:DISPLAY",
                f"DESCRIPTION:Reminder: {_escape_ics_text(summary)}",
                "END:VALARM",
                "END:VEVENT",
            ]
        )

    lines.extend(["END:VCALENDAR", ""])
    return "\r\n".join(lines)
