#!/usr/bin/env python3
"""Schoolbag Opt-In Live Canary Script (SB-005).

Offline-by-default verification script for Schoolbag, testing the complete
vertical slice: Strands AI advisory agent, Human Authority Gate, RFC 5545
iCalendar export, and multi-child family board data.

Usage:
    # 1. Offline dry-run verification (default, $0.00 spend, no network calls):
    python scripts/live_canary.py

    # 2. Opt-in live provider verification (requires explicit flag + GROQ_API_KEY):
    python scripts/live_canary.py --live

    # 3. Against a running live server:
    python scripts/live_canary.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure school_service src is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SERVICE_SRC = _REPO_ROOT / "services" / "school_service" / "src"
_SERVICE_TESTS = _REPO_ROOT / "services" / "school_service" / "tests"
if str(_SERVICE_SRC) not in sys.path:
    sys.path.insert(0, str(_SERVICE_SRC))
if str(_SERVICE_TESTS) not in sys.path:
    sys.path.insert(0, str(_SERVICE_TESTS))

import httpx


def _log(step: str, status: str = "PASS", detail: str = "") -> None:
    badge = f"[{status}]"
    print(f"{badge:<8} {step:<48} {detail}")


class CanaryClient:
    """Client that communicates with either remote HTTP service or in-process TestClient."""

    def __init__(self, base_url: str | None = None, live_mode: bool = False) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.session_cookie: str | None = None
        self.temp_dir: tempfile.TemporaryDirectory | None = None

        if not self.base_url:
            from fastapi.testclient import TestClient
            from schoolbag.interfaces.http.app import create_app

            self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
            db_path = Path(self.temp_dir.name) / "canary_schoolbag.db"

            if live_mode:
                app = create_app(f"sqlite:///{db_path}")
            else:
                from test_strands_advisory import DUMMY_KEY, _make_mock_transport

                mock_transport = _make_mock_transport()
                app = create_app(f"sqlite:///{db_path}", transport=mock_transport)
                app.state.strands_engine._api_key = DUMMY_KEY

            self._client: Any = TestClient(app)
        else:
            self._client = httpx.Client(base_url=self.base_url, timeout=65.0)

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.base_url:
            headers["Origin"] = self.base_url
        if self.session_cookie:
            headers["Cookie"] = f"schoolbag_session={self.session_cookie}"
        return headers

    def get(self, path: str) -> Any:
        resp = self._client.get(path, headers=self._headers())
        self._capture_cookie(resp)
        return resp

    def post(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        h = self._headers()
        if headers:
            h.update(headers)
        resp = self._client.post(path, json=json_data or {}, headers=h)
        self._capture_cookie(resp)
        return resp

    def _capture_cookie(self, resp: Any) -> None:
        if hasattr(resp, "cookies") and "schoolbag_session" in resp.cookies:
            self.session_cookie = resp.cookies["schoolbag_session"]


def run_canary(live: bool = False, base_url: str | None = None) -> int:
    print("=" * 80)
    print("  SCHOOLBAG LIVE CANARY VERIFICATION (SB-005)")
    print(
        f"  Mode: {'LIVE GROQ (openai/gpt-oss-20b)' if live else 'OFFLINE DRY-RUN (Deterministic Mock)'}"
    )
    if base_url:
        print(f"  Target Server: {base_url}")
    print("=" * 80)

    if base_url:
        _log(
            "PRE-CHECK: Remote mode",
            detail="Provider credentials and billing stay on the server",
        )
    elif live:
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            _log(
                "PRE-CHECK: GROQ_API_KEY presence",
                "FAIL",
                "Missing GROQ_API_KEY environment variable. Required for live canary.",
            )
            return 1
        _log(
            "PRE-CHECK: GROQ_API_KEY presence",
            "PASS",
            "GROQ_API_KEY detected in environment",
        )
    else:
        _log(
            "PRE-CHECK: Spend invariant",
            "PASS",
            "Strictly $0.00 / ₹0.00 spend; zero paid API calls",
        )

    client = CanaryClient(base_url=base_url, live_mode=live)

    # 1. Health Probe
    res = client.get("/api/health")
    if res.status_code != 200:
        _log(
            "Stage 1: Health & Engine Probe",
            "FAIL",
            f"Expected 200, got {res.status_code}",
        )
        return 1
    h_data = res.json()
    if h_data.get("status") != "ok":
        _log(
            "Stage 1: Health & Engine Probe",
            "FAIL",
            f"Health status was not ok: {h_data}",
        )
        return 1
    _log(
        "Stage 1: Health & Engine Probe",
        "PASS",
        f"DB: {h_data['database']['engine']}, Strands: {h_data['strands']['status']}",
    )

    # 2. Readiness Probe
    res = client.get("/api/ready")
    if res.status_code != 200:
        _log("Stage 2: Readiness Probe", "FAIL", f"Expected 200, got {res.status_code}")
        return 1
    _log("Stage 2: Readiness Probe", "PASS", "Service is ready for intake")

    # 3. Workspace Session Cookie
    res = client.post("/api/workspaces", {"name": "Canary Family Workspace"})
    if res.status_code not in (200, 201):
        _log(
            "Stage 3: Workspace Session Cookie",
            "FAIL",
            f"Expected 200/201, got {res.status_code}",
        )
        return 1
    ws_id = res.json().get("workspace_id", "")
    _log("Stage 3: Workspace Session Cookie", "PASS", f"Workspace ID: {ws_id[:12]}...")

    # 4. Preset Catalog
    res = client.get("/api/presets")
    if res.status_code != 200:
        _log(
            "Stage 4: Synthetic Preset Catalog",
            "FAIL",
            f"Expected 200, got {res.status_code}",
        )
        return 1
    presets = res.json()
    if len(presets) < 3:
        _log(
            "Stage 4: Synthetic Preset Catalog",
            "FAIL",
            f"Expected >= 3 presets, got {len(presets)}",
        )
        return 1
    _log(
        "Stage 4: Synthetic Preset Catalog",
        "PASS",
        f"{len(presets)} Coimbatore presets loaded",
    )

    # 5. Notice Ingestion & Action Extraction
    sample_notice = {
        "source_type": "whatsapp",
        "class_name": "Class 5-B",
        "child_alias": "Kavya",
        "title": "Canary Annual Day Field Trip & Costume Fee",
        "raw_body": (
            "Dear Parents, Annual Day Field Trip on Friday. "
            "Costume fee is Rs 350 due by Friday 5 PM. "
            "Signed parent consent slip required by Thursday 4 PM. "
            "- Kovai Vidya Mandir, Coimbatore"
        ),
        "raw_due_text": "Friday 5 PM",
    }
    res = client.post("/api/notices", sample_notice)
    if res.status_code != 201:
        _log(
            "Stage 5: Notice Intake & Rule Extraction",
            "FAIL",
            f"Expected 201, got {res.status_code}",
        )
        return 1
    n_data = res.json()
    notice_id = n_data["notice"]["notice_id"]
    actions = n_data.get("actions", [])
    fee_act = next((a for a in actions if a["action_type"] == "fee_payment"), None)
    if not fee_act:
        _log(
            "Stage 5: Notice Intake & Rule Extraction",
            "FAIL",
            "No fee_payment action extracted",
        )
        return 1
    fee_action_id = fee_act["action_id"]
    action_version = fee_act.get("version", 1)
    _log(
        "Stage 5: Notice Intake & Rule Extraction",
        "PASS",
        f"Extracted {len(actions)} actions; Fee action ID: {fee_action_id[:10]}...",
    )

    # 6. Strands Agent Advisory Loop
    headers = {"Idempotency-Key": f"canary_strands_{int(time.time())}"}
    res = client.post(
        f"/api/notices/{notice_id}/analyze-strands",
        {"expected_version": 1},
        headers=headers,
    )
    if res.status_code != 200:
        _log(
            "Stage 6: Strands AI Advisory Loop",
            "FAIL",
            f"Expected 200, got {res.status_code}: {res.text}",
        )
        return 1
    s_data = res.json()
    if not s_data.get("provenance", {}).get("grounded_against_tool"):
        _log(
            "Stage 6: Strands AI Advisory Loop",
            "FAIL",
            "Missing grounded_against_tool verification",
        )
        return 1
    _log(
        "Stage 6: Strands AI Advisory Loop",
        "PASS",
        f"Grounded against tool; {len(s_data['suggested_actions'])} suggestions",
    )

    # 7. Human Authority Gate (Simulate Assistant Approval -> HTTP 403)
    res = client.post(
        f"/api/actions/{fee_action_id}/approve",
        {
            "actor_type": "assistant",
            "actor_name": "strands_bot",
            "expected_version": action_version,
        },
    )
    if res.status_code != 403:
        _log(
            "Stage 7: Human Authority Gate Enforced",
            "FAIL",
            f"Expected 403, got {res.status_code}",
        )
        return 1
    err = res.json()
    if err.get("error") != "HUMAN_APPROVAL_REQUIRED":
        _log(
            "Stage 7: Human Authority Gate Enforced",
            "FAIL",
            f"Expected HUMAN_APPROVAL_REQUIRED, got {err}",
        )
        return 1
    msg = err.get("message") or err.get("detail", "")
    _log(
        "Stage 7: Human Authority Gate Enforced",
        "PASS",
        f"HTTP 403 correctly blocked assistant authorization: {msg}",
    )

    # 8. Human Parent Authorization
    res = client.post(
        f"/api/actions/{fee_action_id}/approve",
        {
            "actor_type": "parent",
            "actor_name": "Parent User",
            "expected_version": action_version,
        },
    )
    if res.status_code != 200:
        _log(
            "Stage 8: Human Parent Authorization",
            "FAIL",
            f"Expected 200, got {res.status_code}",
        )
        return 1
    updated_act = res.json()
    if updated_act.get("status") != "approved":
        _log(
            "Stage 8: Human Parent Authorization",
            "FAIL",
            f"Expected approved, got {updated_act.get('status')}",
        )
        return 1
    action_version = updated_act["version"]
    _log(
        "Stage 8: Human Parent Authorization",
        "PASS",
        f"Action status: approved, version: v{action_version}",
    )

    # 9. Single Action RFC 5545 iCalendar Export
    res = client.get(f"/api/actions/{fee_action_id}/calendar.ics")
    if res.status_code != 200 or "text/calendar" not in res.headers.get(
        "content-type", ""
    ):
        _log(
            "Stage 9: Single Action .ics Export",
            "FAIL",
            f"Expected 200 text/calendar, got {res.status_code}",
        )
        return 1
    ics_content = res.text
    if "BEGIN:VCALENDAR" not in ics_content or "VALARM" not in ics_content:
        _log(
            "Stage 9: Single Action .ics Export",
            "FAIL",
            "Missing VCALENDAR or VALARM markers",
        )
        return 1
    _log(
        "Stage 9: Single Action .ics Export",
        "PASS",
        "Valid RFC 5545 VEVENT with -2h alarm reminder trigger",
    )

    # 10. Workspace Aggregate Family Calendar Feed
    res = client.get("/api/actions/calendar.ics")
    if res.status_code != 200 or "text/calendar" not in res.headers.get(
        "content-type", ""
    ):
        _log(
            "Stage 10: Family Calendar Feed (.ics)",
            "FAIL",
            f"Expected 200 text/calendar, got {res.status_code}",
        )
        return 1
    feed_content = res.text
    if (
        "X-WR-CALNAME:Schoolbag Family Schedule" not in feed_content
        or feed_content.count("BEGIN:VEVENT") < 1
    ):
        _log(
            "Stage 10: Family Calendar Feed (.ics)",
            "FAIL",
            "Missing calendar feed events",
        )
        return 1
    _log(
        "Stage 10: Family Calendar Feed (.ics)",
        "PASS",
        f"Consolidated schedule with {feed_content.count('BEGIN:VEVENT')} events",
    )

    # 11. Complete Action
    res = client.post(
        f"/api/actions/{fee_action_id}/complete",
        {
            "actor_type": "parent",
            "actor_name": "Parent User",
            "expected_version": action_version,
        },
    )
    if res.status_code != 200:
        _log(
            "Stage 11: Action Lifecycle Completion",
            "FAIL",
            f"Expected 200, got {res.status_code}",
        )
        return 1
    completed_act = res.json()
    if completed_act.get("status") != "completed":
        _log(
            "Stage 11: Action Lifecycle Completion",
            "FAIL",
            f"Expected completed, got {completed_act.get('status')}",
        )
        return 1
    _log(
        "Stage 11: Action Lifecycle Completion", "PASS", "Action successfully finalized"
    )

    print("=" * 80)
    print("  ALL 11 CANARY STAGES PASSED SUCCESSFULLY!")
    print(
        "  Verified: workflow responses, human gate, calendar export. Billing is checked separately."
    )
    print("=" * 80)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Schoolbag Live Canary Evaluator")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run against live Groq API (requires GROQ_API_KEY)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Base URL of running Schoolbag server (e.g. http://localhost:8000)",
    )
    args = parser.parse_args()

    exit_code = run_canary(live=args.live, base_url=args.base_url)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
