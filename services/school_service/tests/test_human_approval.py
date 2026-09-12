"""Tests for human parent approval boundaries and optimistic locking."""

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


def test_assistant_cannot_approve_fee_or_consent(client: TestClient) -> None:
    """Assistant and system actors are strictly rejected with 403 on approval gates."""
    client.post("/api/workspaces")

    res = client.post(
        "/api/notices",
        json={
            "source_type": "whatsapp",
            "class_name": "Class 5-B",
            "child_alias": "Kavya",
            "title": "Annual Day Costume Fee & Consent",
            "raw_body": "Costume hire fee ₹300. Please sign the consent slip.",
        },
    )
    assert res.status_code == 201
    actions = res.json()["actions"]
    fee_action = next(a for a in actions if a["action_type"] == "fee_payment")
    consent_action = next(a for a in actions if a["action_type"] == "consent_form")

    # Assistant attempts fee approval -> 403
    res_asst_fee = client.post(
        f"/api/actions/{fee_action['action_id']}/approve",
        json={"expected_version": 1, "actor_type": "assistant", "actor_name": "AI Assistant"},
    )
    assert res_asst_fee.status_code == 403
    assert res_asst_fee.json()["error"] == "HUMAN_APPROVAL_REQUIRED"

    # System attempts consent approval -> 403
    res_sys_consent = client.post(
        f"/api/actions/{consent_action['action_id']}/approve",
        json={"expected_version": 1, "actor_type": "system", "actor_name": "Scheduler Daemon"},
    )
    assert res_sys_consent.status_code == 403
    assert res_sys_consent.json()["error"] == "HUMAN_APPROVAL_REQUIRED"

    # Parent successfully approves both
    res_parent_fee = client.post(
        f"/api/actions/{fee_action['action_id']}/approve",
        json={"expected_version": 1, "actor_type": "parent", "actor_name": "Parent (Mother)"},
    )
    assert res_parent_fee.status_code == 200
    assert res_parent_fee.json()["status"] == "approved"
    assert res_parent_fee.json()["version"] == 2

    res_parent_consent = client.post(
        f"/api/actions/{consent_action['action_id']}/approve",
        json={"expected_version": 1, "actor_type": "parent", "actor_name": "Parent (Father)"},
    )
    assert res_parent_consent.status_code == 200
    assert res_parent_consent.json()["status"] == "approved"
    assert res_parent_consent.json()["version"] == 2


def test_optimistic_locking_conflict(client: TestClient) -> None:
    """Submitting stale expected_version returns HTTP 409 STATE_CONFLICT."""
    client.post("/api/workspaces")

    res = client.post(
        "/api/notices",
        json={
            "source_type": "circular_pdf",
            "class_name": "Class 5-B",
            "child_alias": "Kavya",
            "title": "Field Trip Fee",
            "raw_body": "Field trip ₹500",
        },
    )
    action_id = res.json()["actions"][0]["action_id"]

    # First update succeeds (v1 -> v2)
    res_up1 = client.patch(
        f"/api/actions/{action_id}/deadline",
        json={"expected_version": 1, "raw_deadline": "Tomorrow 10 AM"},
    )
    assert res_up1.status_code == 200
    assert res_up1.json()["version"] == 2

    # Second update using stale expected_version 1 fails with 409
    res_up2 = client.patch(
        f"/api/actions/{action_id}/deadline",
        json={"expected_version": 1, "raw_deadline": "Friday 4 PM"},
    )
    assert res_up2.status_code == 409
    assert res_up2.json()["error"] == "STATE_CONFLICT"
