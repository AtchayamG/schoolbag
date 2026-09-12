"""Tests for content fingerprint deduplication and idempotency records."""

from __future__ import annotations

import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from schoolbag.domain.workflow import compute_notice_fingerprint
from schoolbag.interfaces.http.app import create_app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name
    app = create_app(f"sqlite:///{db_path}")
    with TestClient(app) as test_client:
        yield test_client


def test_fingerprint_normalization_resilience() -> None:
    """Whitespace, tabs, and casing variations produce identical fingerprints."""
    fp1 = compute_notice_fingerprint(
        title="  Science Fair   Circular  ",
        raw_body="Please send ₹100 for kit.\nThank you.",
        source_type="WHATSAPP",
        class_name="Class 5-B",
        child_alias="Kavya",
    )
    fp2 = compute_notice_fingerprint(
        title="science fair circular",
        raw_body="please send ₹100 for kit. thank you.",
        source_type="whatsapp",
        class_name="class 5-b",
        child_alias="kavya",
    )
    assert fp1 == fp2


def test_idempotency_key_replay(client: TestClient) -> None:
    """Submitting identical request with same Idempotency-Key replays exact cached response."""
    client.post("/api/workspaces")

    payload = {
        "source_type": "email",
        "class_name": "Class 5-B",
        "child_alias": "Kavya",
        "title": "PTA Meeting Circular",
        "raw_body": "PTA meeting this Saturday 10 AM.",
        "idempotency_key": "key-idemp-001",
    }
    res1 = client.post("/api/notices", json=payload, headers={"Idempotency-Key": "key-idemp-001"})
    assert res1.status_code == 201
    data1 = res1.json()

    # Replay with same key and payload
    res2 = client.post("/api/notices", json=payload, headers={"Idempotency-Key": "key-idemp-001"})
    assert res2.status_code == 201
    data2 = res2.json()

    assert data1["notice"]["notice_id"] == data2["notice"]["notice_id"]
    assert len(data1["actions"]) == len(data2["actions"])

    # Notices count in workspace remains 1
    res_list = client.get("/api/notices")
    assert len(res_list.json()) == 1


def test_idempotency_conflict_on_altered_payload(client: TestClient) -> None:
    """Reusing an idempotency key with an altered payload returns HTTP 409 IDEMPOTENCY_CONFLICT."""
    client.post("/api/workspaces")

    payload1 = {
        "source_type": "email",
        "class_name": "Class 5-B",
        "child_alias": "Kavya",
        "title": "Annual Day Circular",
        "raw_body": "Costume fee ₹300",
        "idempotency_key": "key-conflict-001",
    }
    res1 = client.post("/api/notices", json=payload1)
    assert res1.status_code == 201

    payload2 = {
        "source_type": "email",
        "class_name": "Class 5-B",
        "child_alias": "Kavya",
        "title": "Annual Day Circular ALTERED",
        "raw_body": "Costume fee ₹500",
        "idempotency_key": "key-conflict-001",
    }
    res2 = client.post("/api/notices", json=payload2)
    assert res2.status_code == 409
    assert res2.json()["error"] == "IDEMPOTENCY_CONFLICT"


def test_header_vs_body_idempotency_mismatch(client: TestClient) -> None:
    """Mismatched Idempotency-Key header and body returns HTTP 422 VALIDATION_ERROR."""
    client.post("/api/workspaces")

    payload = {
        "source_type": "email",
        "class_name": "Class 5-B",
        "child_alias": "Kavya",
        "title": "Mismatch Test",
        "raw_body": "Testing key agreement",
        "idempotency_key": "body-key-1",
    }
    res = client.post("/api/notices", json=payload, headers={"Idempotency-Key": "header-key-2"})
    assert res.status_code == 422
    assert res.json()["error"] == "VALIDATION_ERROR"
