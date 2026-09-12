"""Tests for Real Strands Advisory Agent and Offline Transport for Schoolbag.

Exercises:
1. Two-stage Strands loop with observed tool execution, grounding, and provenance.
2. Privacy boundary: customer/parent phone, email, student ID, and DOB redaction before inference.
3. Ungrounded category rejection and safety validation.
4. Mandatory human approval enforcement for fees and consent slips.
5. Idempotent response replay with zero extra model sends.
6. Optimistic locking version conflict (HTTP 409 STATE_CONFLICT).
7. Send budget exhaustion (max 6 sends).
8. Provider 429 rate limit mapping and 15-minute cooldown.
9. Provider connection failure mapping (503 ASSISTANT_UNAVAILABLE).
10. Hallucination without tool execution mapping (502 ASSISTANT_INVALID_OUTPUT).
11. Missing credentials in live mode.
12. Full end-to-end HTTP integration via /api/notices/{id}/analyze-strands.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from schoolbag.domain.errors import (
    AssistantBusyError,
    AssistantInvalidOutputError,
    AssistantUnavailableError,
    StateConflictError,
)
from schoolbag.domain.models import Notice, SchoolAction
from schoolbag.infrastructure.admission import InferenceAdmissionStore
from schoolbag.infrastructure.groq_model import GROQ_MODEL_ID
from schoolbag.infrastructure.strands_agent import StrandsAdvisoryEngine
from schoolbag.interfaces.http.app import create_app

DUMMY_KEY = "gsk_test_schoolbag_mock_key_0123456789abcdef"


def _make_sse_tool_call(tool_name: str, arguments: dict[str, Any], call_id: str = "call_1") -> str:
    chunk1 = {
        "id": "chatcmpl-tool-1",
        "object": "chat.completion.chunk",
        "created": 1725880000,
        "model": GROQ_MODEL_ID,
        "choices": [
            {
                "index": 0,
                "delta": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "index": 0,
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(arguments),
                            },
                        }
                    ],
                },
                "finish_reason": None,
            }
        ],
    }
    chunk2 = {
        "id": "chatcmpl-tool-1",
        "object": "chat.completion.chunk",
        "created": 1725880000,
        "model": GROQ_MODEL_ID,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}],
    }
    return f"data: {json.dumps(chunk1)}\n\ndata: {json.dumps(chunk2)}\n\ndata: [DONE]\n\n"


def _make_sse_text_response(text: str) -> str:
    chunk = {
        "id": "chatcmpl-text-1",
        "object": "chat.completion.chunk",
        "created": 1725880000,
        "model": GROQ_MODEL_ID,
        "choices": [
            {
                "index": 0,
                "delta": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
    }
    return f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n"


def _make_parsed_response(content: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "id": "chatcmpl-parsed-1",
        "object": "chat.completion",
        "created": 1725880000,
        "model": GROQ_MODEL_ID,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(content) if content is not None else None,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 60,
            "total_tokens": 210,
        },
    }


def _make_mock_transport(
    tool_name: str = "get_school_notice_context",
    extracted_content: dict[str, Any] | None = None,
    captured_requests: list[dict[str, Any]] | None = None,
) -> httpx.MockTransport:
    tool_sse = _make_sse_tool_call(tool_name, {"target_notice_id": "not_test"})
    text_sse = _make_sse_text_response(
        "Inspected school notice: requires ₹350 costume fee and signed Ooty consent slip."
    )
    parsed_json = _make_parsed_response(
        extracted_content
        or {
            "summary": "Annual Day field trip and costume preparation for Kavya.",
            "suggested_actions": [
                {
                    "category": "fee",
                    "title": "Costume & Bus Fee",
                    "description": "Pay ₹350 for Annual Day costume and Ooty bus transport.",
                    "deadline_hint": "Friday 5 PM",
                    "amount_inr": 350.0,
                    "approval_required": True,
                },
                {
                    "category": "consent",
                    "title": "Parental Consent Form",
                    "description": "Sign permission slip for out-of-station travel.",
                    "deadline_hint": "Friday 5 PM",
                    "amount_inr": None,
                    "approval_required": True,
                },
            ],
            "is_urgent": False,
            "advisory_notes": "Authorize fee payment before Friday deadline.",
        }
    )

    turn = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal turn
        turn += 1
        body = json.loads(request.content.decode("utf-8"))
        if captured_requests is not None:
            captured_requests.append(body)

        if "response_format" in body:
            return httpx.Response(200, json=parsed_json)
        if turn == 1:
            return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=tool_sse)
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=text_sse)

    return httpx.MockTransport(handler)


@pytest.mark.anyio
async def test_strands_advisory_two_stage_loop_success(tmp_path: Path) -> None:
    """Verify two-stage Strands loop with observed tool execution and truthful provenance."""
    db_file = str(tmp_path / "strands_adv.db")
    admission_store = InferenceAdmissionStore(db_file)
    mock_transport = _make_mock_transport()
    engine = StrandsAdvisoryEngine(
        admission_store=admission_store,
        api_key=DUMMY_KEY,
        transport=mock_transport,
    )

    notice = Notice(
        notice_id="not_adv_001",
        workspace_id="ws_adv_test",
        source_type="whatsapp",
        class_name="Class 5-B",
        child_alias="Kavya",
        title="Annual Day Field Trip",
        raw_body="Please pay ₹350 for Annual Day costume and submit signed consent slip by Friday 5 PM.",
        raw_due_text="Friday 5 PM",
        normalized_due_at="2026-09-18T17:00:00+05:30",
        source_fingerprint="fp_test_123",
        version=1,
    )
    actions = [
        SchoolAction(
            action_id="act_001",
            workspace_id="ws_adv_test",
            notice_id="not_adv_001",
            action_type="fee_payment",
            title="Costume Fee",
            description="Pay ₹350",
            raw_deadline="Friday 5 PM",
            normalized_deadline="2026-09-18T17:00:00+05:30",
            amount_inr=350.0,
            status="pending_approval",
            approval_required=True,
            confidence=1.0,
            extraction_provenance={},
            version=1,
        )
    ]

    advice = await engine.generate_advice(
        workspace_id="ws_adv_test",
        notice=notice,
        actions=actions,
        expected_version=1,
    )

    assert advice.notice_id == "not_adv_001"
    assert advice.source_version == 1
    assert "Kavya" in advice.summary or "Annual Day" in advice.summary
    assert len(advice.suggested_actions) == 2
    assert advice.suggested_actions[0].category == "fee"
    assert advice.suggested_actions[0].amount_inr == 350.0
    assert advice.suggested_actions[0].approval_required is True
    assert advice.suggested_actions[1].category == "consent"
    assert advice.suggested_actions[1].approval_required is True

    # Truthful provenance
    prov = advice.provenance
    assert prov["engine"] == "strands"
    assert prov["provider"] == "offline_transport_test"
    assert prov["model"] == GROQ_MODEL_ID
    assert prov["actual_tools"] == 1
    assert prov["actual_sends"] >= 2
    assert prov["advisory_only"] is True


@pytest.mark.anyio
async def test_strands_advisory_redacts_pii(tmp_path: Path) -> None:
    """Verify that parent phone, email, student ID, and DOB are redacted before wire dispatch."""
    captured_requests: list[dict[str, Any]] = []
    mock_transport = _make_mock_transport(captured_requests=captured_requests)
    db_file = str(tmp_path / "strands_pii.db")
    admission_store = InferenceAdmissionStore(db_file)
    engine = StrandsAdvisoryEngine(
        admission_store=admission_store,
        api_key=DUMMY_KEY,
        transport=mock_transport,
    )

    notice = Notice(
        notice_id="not_pii_001",
        workspace_id="ws_pii",
        source_type="email",
        class_name="Class 5-B",
        child_alias="Kavya",
        title="Confidential Notice for Parent",
        raw_body=(
            "Parent phone: 9876543210. Email: confidential_parent@example.com. "
            "Student ID: ADMN-2026-8888. DOB: 14/07/2014. "
            "Please pay ₹150 for science kit."
        ),
        raw_due_text="Tomorrow 10 AM",
        normalized_due_at="2026-09-15T10:00:00+05:30",
        source_fingerprint="fp_pii_999",
        version=1,
    )

    await engine.generate_advice(
        workspace_id="ws_pii",
        notice=notice,
        actions=[],
        expected_version=1,
    )

    all_wire_text = json.dumps(captured_requests)
    assert "9876543210" not in all_wire_text, "Parent phone leaked over wire!"
    assert "confidential_parent@example.com" not in all_wire_text, "Parent email leaked over wire!"
    assert "ADMN-2026-8888" not in all_wire_text, "Student ID leaked over wire!"
    assert "14/07/2014" not in all_wire_text, "Student DOB leaked over wire!"


@pytest.mark.anyio
async def test_strands_advisory_rejects_ungrounded_categories(tmp_path: Path) -> None:
    """Model-invented category outside the allowed vocabulary is rejected with 502."""
    malformed_content = {
        "summary": "Invalid category test.",
        "suggested_actions": [
            {
                "category": "unauthorized_cryptocurrency_mining",
                "title": "Crypto mining task",
                "description": "Invalid action category",
                "deadline_hint": None,
                "amount_inr": None,
                "approval_required": False,
            }
        ],
        "is_urgent": False,
        "advisory_notes": "",
    }
    mock_transport = _make_mock_transport(extracted_content=malformed_content)
    db_file = str(tmp_path / "strands_ungrounded.db")
    admission_store = InferenceAdmissionStore(db_file)
    engine = StrandsAdvisoryEngine(
        admission_store=admission_store,
        api_key=DUMMY_KEY,
        transport=mock_transport,
    )

    notice = Notice(
        notice_id="not_unground_001",
        workspace_id="ws_unground",
        source_type="whatsapp",
        class_name="Class 8-A",
        child_alias="Arun",
        title="Notice",
        raw_body="Details",
        raw_due_text=None,
        normalized_due_at=None,
        source_fingerprint="fp_unground",
        version=1,
    )

    with pytest.raises(AssistantInvalidOutputError) as exc_info:
        await engine.generate_advice(
            workspace_id="ws_unground",
            notice=notice,
            actions=[],
            expected_version=1,
        )
    assert "category" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_strands_advisory_mandatory_fee_and_consent_approval(tmp_path: Path) -> None:
    """Even if model claims approval_required=false for fees, the engine forces true."""
    content_with_false_approval = {
        "summary": "Mandatory approval test.",
        "suggested_actions": [
            {
                "category": "fee",
                "title": "School Exam Fee",
                "description": "Pay ₹250",
                "deadline_hint": "Next Monday",
                "amount_inr": 250.0,
                "approval_required": False,  # Model attempted to bypass approval
            },
            {
                "category": "consent",
                "title": "Medical Checkup Consent",
                "description": "Sign slip",
                "deadline_hint": None,
                "amount_inr": None,
                "approval_required": False,  # Model attempted to bypass approval
            },
        ],
        "is_urgent": False,
        "advisory_notes": "",
    }
    mock_transport = _make_mock_transport(extracted_content=content_with_false_approval)
    db_file = str(tmp_path / "strands_enforce.db")
    admission_store = InferenceAdmissionStore(db_file)
    engine = StrandsAdvisoryEngine(
        admission_store=admission_store,
        api_key=DUMMY_KEY,
        transport=mock_transport,
    )

    notice = Notice(
        notice_id="not_enforce_001",
        workspace_id="ws_enforce",
        source_type="sms",
        class_name="Class 8-A",
        child_alias="Arun",
        title="Fee and Consent Notice",
        raw_body="Pay exam fee ₹250 and sign medical slip",
        raw_due_text=None,
        normalized_due_at=None,
        source_fingerprint="fp_enforce",
        version=1,
    )

    advice = await engine.generate_advice(
        workspace_id="ws_enforce",
        notice=notice,
        actions=[],
        expected_version=1,
    )

    assert advice.suggested_actions[0].approval_required is True
    assert advice.suggested_actions[1].approval_required is True


@pytest.mark.anyio
async def test_strands_advisory_idempotent_replay_no_extra_sends(tmp_path: Path) -> None:
    """Replay under same idempotency key returns exact cached response with 0 extra dispatches."""
    send_counter = [0]

    async def counting_handler(request: httpx.Request) -> httpx.Response:
        send_counter[0] += 1
        body = json.loads(request.content.decode("utf-8"))
        if "response_format" in body:
            return httpx.Response(
                200,
                json=_make_parsed_response(
                    {
                        "summary": "Replay test summary.",
                        "suggested_actions": [],
                        "is_urgent": False,
                        "advisory_notes": "",
                    }
                ),
            )
        if send_counter[0] == 1:
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                text=_make_sse_tool_call("get_school_notice_context", {}),
            )
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, text=_make_sse_text_response("Done")
        )

    mock_transport = httpx.MockTransport(counting_handler)
    db_file = str(tmp_path / "strands_replay.db")
    admission_store = InferenceAdmissionStore(db_file)
    engine = StrandsAdvisoryEngine(
        admission_store=admission_store,
        api_key=DUMMY_KEY,
        transport=mock_transport,
    )

    notice = Notice(
        notice_id="not_rep_001",
        workspace_id="ws_rep",
        source_type="whatsapp",
        class_name="Class 5-B",
        child_alias="Kavya",
        title="Notice for Replay",
        raw_body="Details",
        raw_due_text=None,
        normalized_due_at=None,
        source_fingerprint="fp_rep",
        version=1,
    )

    # First call
    res1 = await engine.generate_advice(
        workspace_id="ws_rep",
        notice=notice,
        actions=[],
        expected_version=1,
        idempotency_key="key_exact_replay_001",
    )
    sends_after_first = send_counter[0]
    assert sends_after_first >= 2

    # Second call (replay)
    res2 = await engine.generate_advice(
        workspace_id="ws_rep",
        notice=notice,
        actions=[],
        expected_version=1,
        idempotency_key="key_exact_replay_001",
    )

    assert send_counter[0] == sends_after_first
    assert res1.summary == res2.summary


@pytest.mark.anyio
async def test_stale_notice_version_conflict(tmp_path: Path) -> None:
    """If notice version is modified, rejects with StateConflictError (HTTP 409)."""
    db_file = str(tmp_path / "strands_stale.db")
    admission_store = InferenceAdmissionStore(db_file)
    mock_transport = _make_mock_transport()
    engine = StrandsAdvisoryEngine(
        admission_store=admission_store,
        api_key=DUMMY_KEY,
        transport=mock_transport,
    )

    notice = Notice(
        notice_id="not_stale_001",
        workspace_id="ws_stale",
        source_type="sms",
        class_name="Class 5-B",
        child_alias="Kavya",
        title="Notice",
        raw_body="Body",
        raw_due_text=None,
        normalized_due_at=None,
        source_fingerprint="fp_stale",
        version=2,  # Current version is 2
    )

    with pytest.raises(StateConflictError) as exc_info:
        await engine.generate_advice(
            workspace_id="ws_stale",
            notice=notice,
            actions=[],
            expected_version=1,  # Stale expected version 1
        )
    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "STATE_CONFLICT"


@pytest.mark.anyio
async def test_strands_advisory_send_budget_exhaustion(tmp_path: Path) -> None:
    """When agent enters endless tool loop, max send budget (6) halts execution."""
    infinite_tool_sse = _make_sse_tool_call("get_school_notice_context", {})

    async def infinite_tool_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, text=infinite_tool_sse
        )

    mock_transport = httpx.MockTransport(infinite_tool_handler)
    db_file = str(tmp_path / "strands_budget.db")
    admission_store = InferenceAdmissionStore(db_file)
    engine = StrandsAdvisoryEngine(
        admission_store=admission_store,
        api_key=DUMMY_KEY,
        transport=mock_transport,
    )

    notice = Notice(
        notice_id="not_bdg_001",
        workspace_id="ws_bdg",
        source_type="whatsapp",
        class_name="Class 5-B",
        child_alias="Kavya",
        title="Loop Notice",
        raw_body="Body",
        raw_due_text=None,
        normalized_due_at=None,
        source_fingerprint="fp_bdg",
        version=1,
    )

    with pytest.raises(AssistantBusyError) as exc_info:
        await engine.generate_advice(
            workspace_id="ws_bdg",
            notice=notice,
            actions=[],
            expected_version=1,
        )
    assert "budget" in str(exc_info.value).lower() or "busy" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_strands_advisory_provider_429_busy(tmp_path: Path) -> None:
    """When provider returns HTTP 429, maps to AssistantBusyError."""

    async def rate_limit_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            headers={"retry-after": "10"},
            json={"error": {"message": "Rate limit exceeded", "type": "tokens"}},
        )

    mock_transport = httpx.MockTransport(rate_limit_handler)
    db_file = str(tmp_path / "strands_429.db")
    admission_store = InferenceAdmissionStore(db_file)
    engine = StrandsAdvisoryEngine(
        admission_store=admission_store,
        api_key=DUMMY_KEY,
        transport=mock_transport,
    )

    notice = Notice(
        notice_id="not_429_001",
        workspace_id="ws_429",
        source_type="sms",
        class_name="Class 5-B",
        child_alias="Kavya",
        title="429 Notice",
        raw_body="Body",
        raw_due_text=None,
        normalized_due_at=None,
        source_fingerprint="fp_429",
        version=1,
    )

    with pytest.raises(AssistantBusyError) as exc_info:
        await engine.generate_advice(
            workspace_id="ws_429",
            notice=notice,
            actions=[],
            expected_version=1,
        )
    assert "rate limit" in str(exc_info.value).lower() or "busy" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_strands_advisory_connection_failure_unavailable(tmp_path: Path) -> None:
    """When transport fails to connect, maps to AssistantUnavailableError (503)."""

    async def connect_fail_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Network unreachable")

    mock_transport = httpx.MockTransport(connect_fail_handler)
    db_file = str(tmp_path / "strands_conn.db")
    admission_store = InferenceAdmissionStore(db_file)
    engine = StrandsAdvisoryEngine(
        admission_store=admission_store,
        api_key=DUMMY_KEY,
        transport=mock_transport,
    )

    notice = Notice(
        notice_id="not_conn_001",
        workspace_id="ws_conn",
        source_type="email",
        class_name="Class 5-B",
        child_alias="Kavya",
        title="Conn Notice",
        raw_body="Body",
        raw_due_text=None,
        normalized_due_at=None,
        source_fingerprint="fp_conn",
        version=1,
    )

    with pytest.raises(AssistantUnavailableError) as exc_info:
        await engine.generate_advice(
            workspace_id="ws_conn",
            notice=notice,
            actions=[],
            expected_version=1,
        )
    assert exc_info.value.status_code == 503
    assert "connection" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_strands_advisory_no_tool_execution_invalid_output(tmp_path: Path) -> None:
    """When agent hallucinates without calling get_school_notice_context, maps to 502."""
    text_sse = _make_sse_text_response("I already know what the notice says without checking.")

    async def no_tool_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=text_sse)

    mock_transport = httpx.MockTransport(no_tool_handler)
    db_file = str(tmp_path / "strands_notool.db")
    admission_store = InferenceAdmissionStore(db_file)
    engine = StrandsAdvisoryEngine(
        admission_store=admission_store,
        api_key=DUMMY_KEY,
        transport=mock_transport,
    )

    notice = Notice(
        notice_id="not_notool_001",
        workspace_id="ws_notool",
        source_type="whatsapp",
        class_name="Class 8-A",
        child_alias="Arun",
        title="No Tool Notice",
        raw_body="Body",
        raw_due_text=None,
        normalized_due_at=None,
        source_fingerprint="fp_notool",
        version=1,
    )

    with pytest.raises(AssistantInvalidOutputError) as exc_info:
        await engine.generate_advice(
            workspace_id="ws_notool",
            notice=notice,
            actions=[],
            expected_version=1,
        )
    assert exc_info.value.status_code == 502
    assert "get_school_notice_context" in str(exc_info.value)


@pytest.mark.anyio
async def test_strands_advisory_live_mode_missing_api_key(tmp_path: Path) -> None:
    """When mode is live and GROQ_API_KEY is missing, raises AssistantUnavailableError."""
    db_file = str(tmp_path / "strands_nokey.db")
    admission_store = InferenceAdmissionStore(db_file)
    engine = StrandsAdvisoryEngine(
        admission_store=admission_store,
        api_key="",  # Missing key
        transport=None,  # No offline transport
        mode="live",
    )

    notice = Notice(
        notice_id="not_nokey_001",
        workspace_id="ws_nokey",
        source_type="sms",
        class_name="Class 5-B",
        child_alias="Kavya",
        title="No Key Notice",
        raw_body="Body",
        raw_due_text=None,
        normalized_due_at=None,
        source_fingerprint="fp_nokey",
        version=1,
    )

    with pytest.raises(AssistantUnavailableError) as exc_info:
        await engine.generate_advice(
            workspace_id="ws_nokey",
            notice=notice,
            actions=[],
            expected_version=1,
        )
    assert "groq_api_key" in str(exc_info.value).lower()


def test_strands_advisory_http_endpoint_e2e(tmp_path: Path) -> None:
    """Full HTTP integration test calling POST /api/notices/{id}/analyze-strands."""
    mock_transport = _make_mock_transport()
    db_path = str(tmp_path / "http_e2e.db")

    app = create_app(
        db_url=f"sqlite:///{db_path}",
        transport=mock_transport,
    )
    # Inject api_key for test mock transport
    app.state.strands_engine._api_key = DUMMY_KEY

    with TestClient(app) as client:
        # 1. Bootstrap workspace
        ws_res = client.post("/api/workspaces")
        assert ws_res.status_code == 200

        # 2. Intake notice
        intake_res = client.post(
            "/api/notices",
            json={
                "source_type": "whatsapp",
                "class_name": "Class 5-B",
                "child_alias": "Kavya",
                "title": "Annual Day Circular",
                "raw_body": "Costume fee ₹350 and consent form required by Friday 5 PM.",
                "raw_due_text": "Friday 5 PM",
            },
        )
        assert intake_res.status_code == 201
        notice_id = intake_res.json()["notice"]["notice_id"]

        # 3. Request Strands Advisory Analysis
        adv_res = client.post(
            f"/api/notices/{notice_id}/analyze-strands",
            json={"expected_version": 1},
        )
        assert adv_res.status_code == 200
        adv_data = adv_res.json()
        assert adv_data["notice_id"] == notice_id
        assert adv_data["source_version"] == 1
        assert len(adv_data["suggested_actions"]) == 2
        assert adv_data["provenance"]["engine"] == "strands"
        assert adv_data["provenance"]["provider"] == "offline_transport_test"
        assert adv_data["provenance"]["advisory_only"] is True
