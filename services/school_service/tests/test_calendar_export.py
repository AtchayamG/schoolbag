"""Tests for RFC 5545 iCalendar (.ics) Export in Schoolbag."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from schoolbag.domain.models import Notice, SchoolAction
from schoolbag.infrastructure.calendar import generate_action_ics, generate_workspace_calendar_ics
from schoolbag.interfaces.http.app import create_app


def test_generate_action_ics_structure() -> None:
    action = SchoolAction(
        action_id="act_cal_001",
        workspace_id="ws_test",
        notice_id="not_1",
        action_type="fee_payment",
        title="Pay Costume Fee",
        description="Pay costume fee to teacher",
        raw_deadline="Friday 5 PM",
        normalized_deadline="2026-09-18T17:00:00+05:30",
        amount_inr=350.0,
        status="draft",
        approval_required=True,
        confidence=1.0,
        extraction_provenance={},
        version=1,
    )
    notice = Notice(
        notice_id="not_1",
        workspace_id="ws_test",
        source_type="whatsapp",
        class_name="Class 5-B",
        child_alias="Kavya",
        title="Annual Day Notice",
        raw_body="Please pay costume fee.",
        raw_due_text="Friday 5 PM",
        normalized_due_at="2026-09-18T17:00:00+05:30",
        source_fingerprint="fp_123",
        version=1,
    )

    ics = generate_action_ics(action, notice)
    assert "BEGIN:VCALENDAR" in ics
    assert "VERSION:2.0" in ics
    assert "BEGIN:VEVENT" in ics
    assert "UID:action-act_cal_001@schoolbag.internal" in ics
    assert "[Kavya] Pay Costume Fee (Class 5-B)" in ics
    assert "Amount: ₹350.0 INR" in ics
    assert "BEGIN:VALARM" in ics
    assert "TRIGGER:-PT2H" in ics
    assert "END:VALARM" in ics
    assert "END:VEVENT" in ics
    assert "END:VCALENDAR" in ics


def test_generate_workspace_calendar_ics_multiple() -> None:
    act1 = SchoolAction(
        action_id="act_1",
        workspace_id="ws_test",
        notice_id="not_1",
        action_type="fee_payment",
        title="Costume Fee",
        description="Fee",
        raw_deadline="Friday 5 PM",
        normalized_deadline="2026-09-18T17:00:00+05:30",
        amount_inr=350.0,
        status="draft",
        approval_required=True,
        confidence=1.0,
        extraction_provenance={},
        version=1,
    )
    act2 = SchoolAction(
        action_id="act_2",
        workspace_id="ws_test",
        notice_id="not_2",
        action_type="materials_bring",
        title="Bring Chart Paper",
        description="Chart paper",
        raw_deadline="Tomorrow",
        normalized_deadline="2026-09-15T09:00:00+05:30",
        amount_inr=None,
        status="draft",
        approval_required=False,
        confidence=1.0,
        extraction_provenance={},
        version=1,
    )
    notices = {
        "not_1": Notice(
            notice_id="not_1",
            workspace_id="ws_test",
            source_type="whatsapp",
            class_name="Class 5-B",
            child_alias="Kavya",
            title="Notice 1",
            raw_body="body 1",
            raw_due_text=None,
            normalized_due_at=None,
            source_fingerprint="fp1",
            version=1,
        ),
        "not_2": Notice(
            notice_id="not_2",
            workspace_id="ws_test",
            source_type="circular",
            class_name="Class 8-A",
            child_alias="Arun",
            title="Notice 2",
            raw_body="body 2",
            raw_due_text=None,
            normalized_due_at=None,
            source_fingerprint="fp2",
            version=1,
        ),
    }

    feed = generate_workspace_calendar_ics([act1, act2], notices)
    assert "BEGIN:VCALENDAR" in feed
    assert feed.count("BEGIN:VEVENT") == 2
    assert "[Kavya] Costume Fee (Class 5-B)" in feed
    assert "[Arun] Bring Chart Paper (Class 8-A)" in feed
    assert "END:VCALENDAR" in feed


def test_http_calendar_endpoints(tmp_path: Path) -> None:
    db_path = str(tmp_path / "calendar_test.db")
    app = create_app(f"sqlite:///{db_path}")

    with TestClient(app) as client:
        # Bootstrap
        ws_res = client.post("/api/workspaces")
        assert ws_res.status_code == 200

        # Create notice
        res = client.post(
            "/api/notices",
            json={
                "source_type": "whatsapp",
                "class_name": "Class 5-B",
                "child_alias": "Kavya",
                "title": "Annual Day Circular",
                "raw_body": "Costume fee of Rs 350 due Friday 5 PM.",
                "raw_due_text": "Friday 5 PM",
            },
        )
        assert res.status_code == 201
        data = res.json()
        action_id = data["actions"][0]["action_id"]

        # 1. Download single action .ics
        ics_res = client.get(f"/api/actions/{action_id}/calendar.ics")
        assert ics_res.status_code == 200
        assert "text/calendar" in ics_res.headers["content-type"]
        assert (
            f'filename="schoolbag_action_{action_id}.ics"' in ics_res.headers["content-disposition"]
        )
        assert "BEGIN:VCALENDAR" in ics_res.text
        assert data["actions"][0]["title"] in ics_res.text
        assert "Kavya" in ics_res.text

        # 2. Download aggregate workspace .ics
        feed_res = client.get("/api/actions/calendar.ics")
        assert feed_res.status_code == 200
        assert "text/calendar" in feed_res.headers["content-type"]
        assert 'filename="schoolbag_family_schedule.ics"' in feed_res.headers["content-disposition"]
        assert "BEGIN:VCALENDAR" in feed_res.text
        assert "BEGIN:VEVENT" in feed_res.text

        # 3. 404 for unknown action .ics
        err_res = client.get("/api/actions/act_nonexistent_99/calendar.ics")
        assert err_res.status_code == 404
        assert err_res.json()["error"] == "ACTION_NOT_FOUND"
