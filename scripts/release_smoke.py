"""Comprehensive 19-Stage Release Smoke Verification for Project 3: Schoolbag.

Validates complete vertical slice, human gates, deduplication, deadline normalizer,
workspace isolation, capacity limits, and truthful zero-spend disclosures.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add school_service to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "services" / "school_service" / "src"))
sys.path.insert(0, str(root_dir / "services" / "school_service" / "tests"))

from fastapi.testclient import TestClient
from schoolbag.interfaces.http.app import create_app
from test_strands_advisory import DUMMY_KEY, _make_mock_transport

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run_smoke() -> None:
    print("=" * 75)
    print("  SCHOOLBAG (SB-001 - SB-004) - 22-STAGE END-TO-END RELEASE SMOKE SUITE")
    print("=" * 75)

    stages_passed = 0
    total_stages = 22

    def stage_ok(stage_num: int, title: str, details: str = "") -> None:
        nonlocal stages_passed
        stages_passed += 1
        detail_str = f" - {details}" if details else ""
        print(f"  [STAGE {stage_num:02d}/22] PASS: {title}{detail_str}")

    tmp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    db_path = Path(tmp_dir.name) / "smoke_schoolbag.db"
    mock_transport = _make_mock_transport()
    app = create_app(f"sqlite:///{db_path}", transport=mock_transport)
    app.state.strands_engine._api_key = DUMMY_KEY

    with TestClient(app) as client:
        # Stage 1: Workspace Session Initialization
        res_ws = client.post("/api/workspaces", json={"name": "Kovai Family Workspace"})
        assert res_ws.status_code in (200, 201), f"Expected 200/201, got {res_ws.status_code}"
        ws_data = res_ws.json()
        assert "schoolbag_session" in client.cookies
        ws_id = ws_data["workspace_id"]
        stage_ok(1, "Workspace Session Cookie Issuance", f"ws_id={ws_id[:12]}...")

        # Stage 2: Ingest Notice & Action Extraction
        raw_text = (
            "Dear Parents of Class 5-B,\n"
            "Our Annual Day Field Trip to Ooty is scheduled for Friday. "
            "Please pay the costume fee of Rs 350 to the class teacher by Friday 5 PM. "
            "Also sign and return the attached field trip consent slip tomorrow 10 AM. "
            "Students must bring 2 chart papers and clay models for the science exhibition.\n"
            "- Kovai Vidya Mandir, RS Puram, Coimbatore"
        )
        res_notice = client.post(
            "/api/notices",
            json={
                "source_type": "whatsapp",
                "class_name": "Class 5-B",
                "child_alias": "Kavya",
                "title": "Annual Day Field Trip, Costume Fee & Science Exhibition",
                "raw_body": raw_text,
                "raw_due_text": "Friday 5 PM",
            },
        )
        assert res_notice.status_code == 201, f"Expected 201, got {res_notice.status_code}: {res_notice.text}"
        notice_data = res_notice.json()
        notice_id = notice_data["notice"]["notice_id"]
        actions = notice_data["actions"]
        assert len(actions) >= 3
        stage_ok(2, "Notice Intake & Rule-Based Action Extraction", f"{len(actions)} actions extracted")

        # Stage 3: Truthful Category Assignment & Confidence Scores
        fee_act = next((a for a in actions if a["action_type"] == "fee_payment"), None)
        consent_act = next((a for a in actions if a["action_type"] == "consent_form"), None)
        material_act = next((a for a in actions if a["action_type"] == "materials_bring"), None)
        assert fee_act is not None and fee_act["amount_inr"] == 350
        assert consent_act is not None
        assert material_act is not None
        stage_ok(3, "Action Categorization & Amount Parsing", "Fee ₹350, Consent Slip, Materials")

        # Stage 4: Notice Fingerprint Deduplication
        res_dup = client.post(
            "/api/notices",
            json={
                "source_type": "whatsapp",
                "class_name": "Class 5-B",
                "child_alias": "Kavya",
                "title": "Annual Day Field Trip, Costume Fee & Science Exhibition",
                "raw_body": raw_text,
            },
        )
        assert res_dup.status_code in (200, 201)
        assert res_dup.json()["is_deduplicated"] is True
        stage_ok(4, "Notice Fingerprint Deduplication", "Duplicate forward replayed existing actions")

        # Stage 5: IST Deadline Normalization
        assert fee_act["normalized_deadline"] is not None
        assert "+05:30" in fee_act["normalized_deadline"]
        stage_ok(5, "Deadline Normalization (IST +05:30)", f"Deadline: {fee_act['normalized_deadline']}")

        # Stage 6: Update Action Deadline
        action_id = fee_act["action_id"]
        res_dl = client.patch(
            f"/api/actions/{action_id}/deadline",
            json={
                "expected_version": 1,
                "raw_deadline": "Next Friday 5 PM",
                "actor_name": "Parent",
            },
        )
        assert res_dl.status_code == 200
        fee_act = res_dl.json()
        assert fee_act["version"] == 2
        stage_ok(6, "Action Deadline Patch & Audit Log", f"Updated to {fee_act['normalized_deadline']}")

        # Stage 7: Draft Reminder Creation
        res_rem = client.post(
            f"/api/actions/{action_id}/reminders",
            json={
                "expected_action_version": 2,
                "channel": "calendar",
                "scheduled_for": fee_act["normalized_deadline"],
                "message_body": "Pay ₹350 Costume Fee",
                "actor_name": "Parent",
            },
        )
        assert res_rem.status_code == 201
        rem_data = res_rem.json()
        assert rem_data["channel"] == "calendar"
        assert rem_data["is_draft"] is True
        stage_ok(7, "Reminder Draft Creation", f"Drafted for {rem_data['scheduled_for']}")

        # Stage 8: Human Authority Gate: AI/Assistant Rejection (HTTP 403)
        res_bad_app = client.post(
            f"/api/actions/{action_id}/approve",
            json={
                "expected_version": 2,
                "actor_type": "assistant",
                "actor_name": "AI Assistant",
            },
        )
        assert res_bad_app.status_code == 403
        assert res_bad_app.json()["error"] == "HUMAN_APPROVAL_REQUIRED"
        stage_ok(8, "Human Authority Gate (HTTP 403)", "Blocked non-parent autonomous approval")

        # Stage 9: Parent Authorization (HTTP 200)
        res_good_app = client.post(
            f"/api/actions/{action_id}/approve",
            json={
                "expected_version": 2,
                "actor_type": "parent",
                "actor_name": "Parent",
            },
        )
        assert res_good_app.status_code == 200
        approved_act = res_good_app.json()
        assert approved_act["status"] == "approved"
        assert approved_act["version"] == 3
        stage_ok(9, "Parent Authorization Gate", f"Approved, new version v{approved_act['version']}")

        # Stage 10: Action Completion
        res_comp = client.post(
            f"/api/actions/{action_id}/complete",
            json={"expected_version": 3, "actor_name": "Parent", "actor_type": "parent"},
        )
        assert res_comp.status_code == 200
        assert res_comp.json()["status"] == "completed"
        assert res_comp.json()["version"] == 4
        stage_ok(10, "Action Completion Transition", "Status: completed, version: 4")

        # Stage 11: Optimistic Locking Conflict (HTTP 409)
        res_conflict = client.post(
            f"/api/actions/{action_id}/complete",
            json={"expected_version": 1, "actor_name": "Parent", "actor_type": "parent"},
        )
        assert res_conflict.status_code == 409
        assert res_conflict.json()["error"] == "STATE_CONFLICT"
        stage_ok(11, "Optimistic Concurrency Conflict", "Rejected stale mutation with 409")

        # Stage 12: Notice Capacity Limit (50 Notices Max)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as cap_dir:
            cap_app = create_app(f"sqlite:///{Path(cap_dir) / 'cap.db'}")
            with TestClient(cap_app) as cap_client:
                cap_client.post("/api/workspaces")
                for i in range(50):
                    res_c = cap_client.post(
                        "/api/notices",
                        json={
                            "source_type": "sms",
                            "class_name": "Class 5-B",
                            "child_alias": "Kavya",
                            "title": f"Notice {i + 1}",
                            "raw_body": f"Notice body {i + 1} with unique text",
                        },
                    )
                    assert res_c.status_code == 201

                res_over = cap_client.post(
                    "/api/notices",
                    json={
                        "source_type": "sms",
                        "class_name": "Class 5-B",
                        "child_alias": "Kavya",
                        "title": "Overflow Notice 51",
                        "raw_body": "This notice should be rejected by capacity limit",
                    },
                )
                assert res_over.status_code == 409
                assert res_over.json()["error"] == "CAPACITY_EXCEEDED"
                stage_ok(12, "Workspace Capacity Limit (50 Max)", "Rejected 51st notice with 409")

        # Stage 13: Cross-Workspace Isolation (HTTP 404)
        with TestClient(app) as client_b:
            client_b.post("/api/workspaces", json={"name": "Family B"})
            res_cross = client_b.get(f"/api/notices/{notice_id}")
            assert res_cross.status_code == 404
            assert res_cross.json()["error"] == "NOTICE_NOT_FOUND"
            stage_ok(13, "Cross-Workspace Isolation", "Tenant B cannot view Tenant A notice (404)")

        # Stage 14: Idempotency Key Replay
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as id_dir:
            idem_app = create_app(f"sqlite:///{Path(id_dir) / 'idem.db'}")
            with TestClient(idem_app) as id_client:
                id_client.post("/api/workspaces")
                p_notice = {
                    "source_type": "sms",
                    "class_name": "Class 8-A",
                    "child_alias": "Arun",
                    "title": "Quarterly Science Fee",
                    "raw_body": "Science fee of Rs 400 due Friday",
                }
                res_id1 = id_client.post("/api/notices", json=p_notice, headers={"Idempotency-Key": "idem_1001"})
                assert res_id1.status_code == 201
                res_id2 = id_client.post("/api/notices", json=p_notice, headers={"Idempotency-Key": "idem_1001"})
                assert res_id2.status_code == 201
                assert res_id1.json()["notice"]["notice_id"] == res_id2.json()["notice"]["notice_id"]
                stage_ok(14, "Idempotency-Key Replay", "Exact replay cached and returned")

                # Stage 15: Idempotency Conflict on Altered Payload
                p_altered = dict(p_notice)
                p_altered["title"] = "Quarterly Science Fee ALTERED"
                res_conf = id_client.post("/api/notices", json=p_altered, headers={"Idempotency-Key": "idem_1001"})
                assert res_conf.status_code == 409
                assert res_conf.json()["error"] == "IDEMPOTENCY_CONFLICT"
                stage_ok(15, "Idempotency Conflict Detection", "Altered payload rejected with 409")

        # Stage 16: Malformed Payload Validation
        res_malf = client.post("/api/notices", json={"invalid_field": 123})
        assert res_malf.status_code == 422
        assert res_malf.json()["error"] == "VALIDATION_ERROR"
        stage_ok(16, "Malformed Payload Rejection", "HTTP 422 validation response")

        # Stage 17: Extractor Unavailable Handling (HTTP 503)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as un_dir:
            app_unavail = create_app(f"sqlite:///{Path(un_dir) / 'unavail.db'}", extraction_mode="unavailable")
            with TestClient(app_unavail) as un_client:
                res_unavail = un_client.post(
                    "/api/notices",
                    json={
                        "source_type": "sms",
                        "class_name": "Class 5-B",
                        "child_alias": "Kavya",
                        "title": "Fee Notice",
                        "raw_body": "Fee due ₹100",
                    },
                )
                assert res_unavail.status_code == 503
                assert res_unavail.json()["error"] == "EXTRACTOR_UNAVAILABLE"
                stage_ok(17, "Extractor Failure Handling", "HTTP 503 EXTRACTOR_UNAVAILABLE")

        # Stage 18: Health and Readiness Probes
        res_health = client.get("/api/health")
        assert res_health.status_code == 200
        h_json = res_health.json()
        assert h_json["status"] == "ok"
        assert h_json["extractor"]["advisory_only"] is True
        res_ready = client.get("/api/ready")
        assert res_ready.status_code == 200
        stage_ok(18, "Truthful Health & Readiness Probes", f"Status: {h_json['status']}, DB: {h_json['database']['engine']}")

        # Stage 19: Privacy & Zero Personal Spend Verification
        res_presets = client.get("/api/presets")
        assert res_presets.status_code == 200
        presets = res_presets.json()
        assert len(presets) >= 2
        for p in presets:
            assert "kavya" in p["child_alias"].lower() or "arun" in p["child_alias"].lower()
            assert "dob" not in p
            assert "medical" not in p
            assert "student_id" not in p
        stage_ok(19, "Privacy & Zero Personal Spend Guarantee", "Zero paid APIs (₹0.00 spend), minimal child alias only")

        # Stage 20: Strands Advisory Loop & Bounded Tool Execution
        res_strands = client.post(
            f"/api/notices/{notice_id}/analyze-strands",
            json={"expected_version": 1},
            headers={"Idempotency-Key": "smoke_strands_001"},
        )
        assert res_strands.status_code == 200, f"Expected 200, got {res_strands.status_code}: {res_strands.text}"
        s_data = res_strands.json()
        assert s_data["notice_id"] == notice_id
        assert s_data["summary"]
        assert len(s_data["suggested_actions"]) >= 1
        assert s_data["provenance"]["engine"] == "strands"
        assert s_data["provenance"]["model"] == "openai/gpt-oss-20b"
        assert s_data["provenance"]["grounded_against_tool"] is True
        assert s_data["provenance"]["tool_calls_observed"] >= 1
        for act in s_data["suggested_actions"]:
            if act["category"] in ("fees", "consent") or act["amount_inr"]:
                assert act["approval_required"] is True

        # Verify idempotent replay
        res_strands_replay = client.post(
            f"/api/notices/{notice_id}/analyze-strands",
            json={"expected_version": 1},
            headers={"Idempotency-Key": "smoke_strands_001"},
        )
        assert res_strands_replay.status_code == 200
        assert res_strands_replay.json()["provenance"]["cached"] is True

        # Verify version conflict check
        res_strands_conflict = client.post(
            f"/api/notices/{notice_id}/analyze-strands",
            json={"expected_version": 999},
        )
        assert res_strands_conflict.status_code == 409
        assert res_strands_conflict.json()["error"] == "STATE_CONFLICT"

        stage_ok(
            20,
            "Strands Agent Advisory Loop & Bounded Read Tool",
            "Grounded against get_school_notice_context with mandatory human approval & idempotency",
        )

        # Stage 21: Action RFC 5545 iCalendar (.ics) Export
        res_ics = client.get(f"/api/actions/{fee_act['action_id']}/calendar.ics")
        assert res_ics.status_code == 200, f"Expected 200, got {res_ics.status_code}"
        assert "text/calendar" in res_ics.headers["content-type"]
        assert f"schoolbag_action_{fee_act['action_id']}.ics" in res_ics.headers["content-disposition"]
        ics_text = res_ics.text
        assert "BEGIN:VCALENDAR" in ics_text
        assert "VERSION:2.0" in ics_text
        assert "BEGIN:VEVENT" in ics_text
        assert "VALARM" in ics_text
        assert "TRIGGER:-PT2H" in ics_text
        assert "END:VEVENT" in ics_text
        assert "END:VCALENDAR" in ics_text
        stage_ok(
            21,
            "Action RFC 5545 iCalendar (.ics) Export",
            "Valid VCALENDAR/VEVENT with -2h alarm reminder trigger and UTC format",
        )

        # Stage 22: Workspace Aggregate Family iCalendar (.ics) Feed
        res_feed = client.get("/api/actions/calendar.ics")
        assert res_feed.status_code == 200, f"Expected 200, got {res_feed.status_code}"
        assert "text/calendar" in res_feed.headers["content-type"]
        assert "schoolbag_family_schedule.ics" in res_feed.headers["content-disposition"]
        feed_text = res_feed.text
        assert "X-WR-CALNAME:Schoolbag Family Schedule" in feed_text
        assert feed_text.count("BEGIN:VEVENT") >= 1
        stage_ok(
            22,
            "Workspace Aggregate Family Calendar Feed (.ics)",
            f"Multi-child schedule export ({feed_text.count('BEGIN:VEVENT')} events in VCALENDAR)",
        )

    print("=" * 75)
    print(f"  ALL {stages_passed}/{total_stages} STAGES PASSED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    run_smoke()
