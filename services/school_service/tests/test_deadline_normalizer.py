"""Tests for deadline normalization and timezone handling."""

from __future__ import annotations

from datetime import datetime

from schoolbag.infrastructure.normalizer import IST, normalize_deadline


def test_iso_format_passthrough() -> None:
    """Valid ISO datetime strings are preserved with timezone."""
    iso_with_tz = "2026-09-18T17:00:00+05:30"
    assert normalize_deadline(iso_with_tz) == iso_with_tz

    iso_raw = "2026-09-18T17:00:00"
    assert normalize_deadline(iso_raw) == "2026-09-18T17:00:00+05:30"


def test_date_string_normalization() -> None:
    """Simple date strings are normalized to 17:00 IST on that date."""
    assert normalize_deadline("2026-09-25") == "2026-09-25T17:00:00+05:30"


def test_relative_weekday_normalization() -> None:
    """Relative weekday references are calculated deterministically in IST."""
    # Reference: Monday Sep 14, 2026 09:00 IST
    ref_dt = datetime(2026, 9, 14, 9, 0, 0, tzinfo=IST)

    norm_fri = normalize_deadline("Friday 5 PM", base_dt=ref_dt)
    assert norm_fri == "2026-09-18T17:00:00+05:30"

    norm_thu = normalize_deadline("Thursday 10 AM", base_dt=ref_dt)
    assert norm_thu == "2026-09-17T10:00:00+05:30"

    norm_tomorrow = normalize_deadline("Tomorrow 2 PM", base_dt=ref_dt)
    assert norm_tomorrow == "2026-09-15T14:00:00+05:30"

    norm_urgent = normalize_deadline("Urgent today", base_dt=ref_dt)
    assert norm_urgent == "2026-09-14T18:00:00+05:30"
