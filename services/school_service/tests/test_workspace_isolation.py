"""Tests for workspace isolation, session cookies, and capacity limits."""

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


def test_session_cookie_issuance(client: TestClient) -> None:
    """Visiting /api/workspaces issues a 32-byte opaque session token via HttpOnly cookie."""
    res = client.post("/api/workspaces")
    assert res.status_code == 200
    data = res.json()
    assert data["workspace_id"].startswith("ws_")
    assert "schoolbag_session" in client.cookies
    token = client.cookies["schoolbag_session"]
    assert len(token) == 64  # 32 bytes hex


def test_cross_workspace_404_isolation(client: TestClient) -> None:
    """Workspace B cannot access or mutate notices belonging to Workspace A."""
    # Workspace A creates notice
    client.cookies.clear()
    res_a = client.post("/api/workspaces")
    ws_a = res_a.json()["workspace_id"]

    res_notice = client.post(
        "/api/notices",
        json={
            "source_type": "whatsapp",
            "class_name": "Class 5-B",
            "child_alias": "Kavya",
            "title": "A's Private Circular",
            "raw_body": "Fee due ₹100",
        },
    )
    assert res_notice.status_code == 201
    notice_id = res_notice.json()["notice"]["notice_id"]
    action_id = res_notice.json()["actions"][0]["action_id"]

    # Switch to Workspace B
    client.cookies.clear()
    res_b = client.post("/api/workspaces")
    ws_b = res_b.json()["workspace_id"]
    assert ws_a != ws_b

    # Workspace B attempts to get A's notice -> 404
    res_get = client.get(f"/api/notices/{notice_id}")
    assert res_get.status_code == 404
    assert res_get.json()["error"] == "NOTICE_NOT_FOUND"

    # Workspace B attempts to update A's action deadline -> 404
    res_patch = client.patch(
        f"/api/actions/{action_id}/deadline",
        json={"expected_version": 1, "raw_deadline": "Monday 10 AM"},
    )
    assert res_patch.status_code == 404
    assert res_patch.json()["error"] == "ACTION_NOT_FOUND"

    # Workspace B list notices is empty
    res_list_b = client.get("/api/notices")
    assert res_list_b.status_code == 200
    assert len(res_list_b.json()) == 0


def test_workspace_notice_capacity_limit(client: TestClient) -> None:
    """Workspace cannot exceed 50 notices maximum."""
    client.post("/api/workspaces")

    # Ensure session workspace is initialized
    store = client.app.state.store  # type: ignore[attr-defined]
    _ = store.get_or_create_workspace(client.cookies["schoolbag_session"])

    for i in range(50):
        res = client.post(
            "/api/notices",
            json={
                "source_type": "sms",
                "class_name": "Class 5-B",
                "child_alias": "Kavya",
                "title": f"Notice {i + 1}",
                "raw_body": f"Details for notice {i + 1} with unique text {i}",
            },
        )
        assert res.status_code == 201

    # 51st notice must be rejected with 409 CAPACITY_EXCEEDED
    res_51 = client.post(
        "/api/notices",
        json={
            "source_type": "sms",
            "class_name": "Class 5-B",
            "child_alias": "Kavya",
            "title": "Notice 51",
            "raw_body": "This notice breaches capacity limit",
        },
    )
    assert res_51.status_code == 409
    assert res_51.json()["error"] == "CAPACITY_EXCEEDED"
