"""Comprehensive test for the required 9-step Schoolbag vertical slice."""

from __future__ import annotations

import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from schoolbag.interfaces.http.app import create_app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name
    app = create_app(f"sqlite:///{db_path}")
    with TestClient(app) as test_client:
        yield test_client


def test_required_vertical_slice(client: TestClient) -> None:
    """Execute and assert all 9 steps of the required Schoolbag vertical slice."""

    # 1. Create an isolated public workbench
    res_ws = client.post("/api/workspaces")
    assert res_ws.status_code == 200
    ws_data = res_ws.json()
    assert ws_data["workspace_id"].startswith("ws_")
    assert "schoolbag_session" in client.cookies
    assert ws_data["capacity_limit"] == 50
    assert ws_data["notice_count"] == 0

    # 2. Add a synthetic school notice
    notice_payload = {
        "source_type": "whatsapp",
        "class_name": "Class 5-B",
        "child_alias": "Kavya",
        "title": "Science Exhibition Project Kit & Materials",
        "raw_body": (
            "Dear Parents of Class 5-B, for our upcoming Science Exhibition on Friday, "
            "each student must pay ₹150 towards the customized science experiment kit. "
            "Please also send 1 white chart paper and craft scissors with your child by Thursday. "
            "— Mrs. Revathi, Kovai Vidya Mandir, RS Puram, Coimbatore."
        ),
        "raw_due_text": "Friday 5 PM",
    }
    res_notice = client.post("/api/notices", json=notice_payload)
    assert res_notice.status_code == 201
    notice_data = res_notice.json()
    notice = notice_data["notice"]
    actions = notice_data["actions"]
    assert notice["title"] == notice_payload["title"]
    assert notice["class_name"] == "Class 5-B"
    assert notice["child_alias"] == "Kavya"
    assert notice["version"] == 1
    assert notice_data["is_deduplicated"] is False

    # 3. Extract at least two actions with provenance and confidence
    assert len(actions) >= 2
    fee_action = next((a for a in actions if a["action_type"] == "fee_payment"), None)
    materials_action = next((a for a in actions if a["action_type"] == "materials_bring"), None)
    assert fee_action is not None, "Fee payment action must be extracted"
    assert materials_action is not None, "Materials to bring action must be extracted"

    assert fee_action["amount_inr"] == 150.0
    assert fee_action["approval_required"] is True
    assert fee_action["confidence"] >= 0.90
    assert fee_action["extraction_provenance"]["engine"] == "deterministic"
    assert fee_action["extraction_provenance"]["provider"] == "synthetic"
    assert fee_action["extraction_provenance"]["advisory_only"] is True

    # 4. Deduplicate the same notice and prove second submission replays without duplicate actions
    res_dup = client.post("/api/notices", json=notice_payload)
    assert res_dup.status_code == 200 or res_dup.status_code == 201
    dup_data = res_dup.json()
    assert dup_data["is_deduplicated"] is True
    assert dup_data["notice"]["notice_id"] == notice["notice_id"]
    assert len(dup_data["actions"]) == len(actions)

    # Verify total notices count in workspace is still 1
    res_list = client.get("/api/notices")
    assert res_list.status_code == 200
    all_notices = res_list.json()
    assert len(all_notices) == 1

    # 5. Edit a deadline and show normalized date/time plus audit event
    action_id = fee_action["action_id"]
    res_deadline = client.patch(
        f"/api/actions/{action_id}/deadline",
        json={
            "expected_version": 1,
            "raw_deadline": "Next Friday 5 PM",
            "actor_name": "Kavya's Mother",
        },
    )
    assert res_deadline.status_code == 200
    updated_action = res_deadline.json()
    assert updated_action["version"] == 2
    assert updated_action["raw_deadline"] == "Next Friday 5 PM"
    assert updated_action["normalized_deadline"] is not None
    assert "+05:30" in updated_action["normalized_deadline"]

    # Verify audit event recorded for deadline normalization
    res_audit = client.get("/api/audit", params={"entity_id": action_id})
    assert res_audit.status_code == 200
    audit_events = res_audit.json()
    deadline_audit = next((e for e in audit_events if e["action"] == "deadline_normalized"), None)
    assert deadline_audit is not None
    assert deadline_audit["version_before"] == 1
    assert deadline_audit["version_after"] == 2
    assert deadline_audit["actor_name"] == "Kavya's Mother"

    # 6. Create a reminder/calendar draft
    res_reminder = client.post(
        f"/api/actions/{action_id}/reminders",
        json={
            "expected_action_version": 2,
            "channel": "calendar",
            "scheduled_for": updated_action["normalized_deadline"],
            "message_body": "Pay ₹150 for Science Kit to Mrs. Revathi",
            "actor_name": "Kavya's Mother",
        },
    )
    assert res_reminder.status_code == 201
    reminder_data = res_reminder.json()
    assert reminder_data["reminder_id"].startswith("rem_")
    assert reminder_data["is_draft"] is True
    assert reminder_data["channel"] == "calendar"

    # 7. Attempt payment/consent as the assistant and return an explicit human-approval error
    res_assistant_approve = client.post(
        f"/api/actions/{action_id}/approve",
        json={
            "expected_version": 2,
            "actor_type": "assistant",
            "actor_name": "AI Assistant",
        },
    )
    assert res_assistant_approve.status_code == 403
    err_data = res_assistant_approve.json()
    assert err_data["error"] == "HUMAN_APPROVAL_REQUIRED"
    assert "explicit human parent approval" in err_data["message"]

    # 8. Approve the draft as a parent, complete it, refresh, and verify persistence
    # Parent approval
    res_parent_approve = client.post(
        f"/api/actions/{action_id}/approve",
        json={
            "expected_version": 2,
            "actor_type": "parent",
            "actor_name": "Kavya's Mother",
        },
    )
    assert res_parent_approve.status_code == 200
    approved_data = res_parent_approve.json()
    assert approved_data["status"] == "approved"
    assert approved_data["version"] == 3
    assert approved_data["approved_by"] == "Kavya's Mother"
    assert approved_data["approved_at"] is not None

    # Parent completion
    res_complete = client.post(
        f"/api/actions/{action_id}/complete",
        json={
            "expected_version": 3,
            "actor_type": "parent",
            "actor_name": "Kavya's Mother",
        },
    )
    assert res_complete.status_code == 200
    completed_data = res_complete.json()
    assert completed_data["status"] == "completed"
    assert completed_data["version"] == 4
    assert completed_data["completed_by"] == "Kavya's Mother"

    # Refresh notice aggregate and verify persistence
    notice_id = notice["notice_id"]
    res_refresh = client.get(f"/api/notices/{notice_id}")
    assert res_refresh.status_code == 200
    aggregate = res_refresh.json()
    refreshed_action = next(a for a in aggregate["actions"] if a["action_id"] == action_id)
    assert refreshed_action["status"] == "completed"
    assert refreshed_action["version"] == 4
    assert len(aggregate["reminders"]) == 1
    assert aggregate["reminders"][0]["is_draft"] is True
    assert len(aggregate["audit_events"]) >= 3

    # 9. Show honest failure states for malformed input and unavailable extraction provider
    # Malformed payload (missing required title/class) -> 422 Unprocessable Entity
    res_malformed = client.post("/api/notices", json={"invalid_field": "data"})
    assert res_malformed.status_code == 422
    assert res_malformed.json()["error"] == "VALIDATION_ERROR"

    # Unavailable extractor -> HTTP 503
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_db = f"{tmp_dir}/unavail.db"
        app_unavail = create_app(f"sqlite:///{tmp_db}", extraction_mode="unavailable")
        with TestClient(app_unavail) as unavail_client:
            res_unavail = unavail_client.post(
                "/api/notices",
                json={
                    "source_type": "sms",
                    "class_name": "Class 5-B",
                    "child_alias": "Kavya",
                    "title": "School Fee",
                    "raw_body": "Fee due ₹200",
                },
            )
            assert res_unavail.status_code == 503
            assert res_unavail.json()["error"] == "EXTRACTOR_UNAVAILABLE"
