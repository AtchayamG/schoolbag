"""Concurrency, two-connection contention, and real PostgreSQL 16.10 verification."""

from __future__ import annotations

import threading
from collections.abc import Generator

import pytest
from disposable_postgres import DisposablePostgresCluster, find_pg_bin
from fastapi.testclient import TestClient

from schoolbag.interfaces.http.app import create_app


@pytest.fixture(scope="module")
def pg_cluster() -> Generator[DisposablePostgresCluster | None, None, None]:
    pg_bin = find_pg_bin()
    if not pg_bin:
        yield None
        return

    cluster = DisposablePostgresCluster(pg_bin)
    try:
        cluster.start()
        yield cluster
    finally:
        cluster.stop()


def test_postgres_full_workflow_slice(pg_cluster: DisposablePostgresCluster | None) -> None:
    """Execute complete 9-step Schoolbag slice against real PostgreSQL 16.10."""
    if pg_cluster is None:
        pytest.skip("Local PostgreSQL 16.10 binaries not available")

    db_url = pg_cluster.create_isolated_db("sb_slice")
    app = create_app(db_url)
    with TestClient(app) as client:
        # 1. Workspace
        res_ws = client.post("/api/workspaces")
        assert res_ws.status_code == 200
        assert "schoolbag_session" in client.cookies

        # 2. Add Notice
        res_notice = client.post(
            "/api/notices",
            json={
                "source_type": "whatsapp",
                "class_name": "Class 5-B",
                "child_alias": "Kavya",
                "title": "Annual Day Cultural Dance",
                "raw_body": "Costume hire fee ₹300. Please sign the consent slip by Wednesday.",
                "raw_due_text": "Wednesday 4 PM",
            },
        )
        assert res_notice.status_code == 201
        data = res_notice.json()
        notice_id = data["notice"]["notice_id"]
        actions = data["actions"]
        assert len(actions) >= 2

        # 3. Deduplication replay on PostgreSQL
        res_dup = client.post(
            "/api/notices",
            json={
                "source_type": "whatsapp",
                "class_name": "Class 5-B",
                "child_alias": "Kavya",
                "title": "Annual Day Cultural Dance",
                "raw_body": "Costume hire fee ₹300. Please sign the consent slip by Wednesday.",
                "raw_due_text": "Wednesday 4 PM",
            },
        )
        assert res_dup.status_code == 200 or res_dup.status_code == 201
        assert res_dup.json()["is_deduplicated"] is True

        # 4. Deadline Edit
        fee_action = next(a for a in actions if a["action_type"] == "fee_payment")
        act_id = fee_action["action_id"]
        res_deadline = client.patch(
            f"/api/actions/{act_id}/deadline",
            json={"expected_version": 1, "raw_deadline": "Wednesday 6 PM", "actor_name": "Father"},
        )
        assert res_deadline.status_code == 200
        assert res_deadline.json()["version"] == 2

        # 5. Reminder draft
        res_rem = client.post(
            f"/api/actions/{act_id}/reminders",
            json={
                "expected_action_version": 2,
                "channel": "sms_draft",
                "scheduled_for": res_deadline.json()["normalized_deadline"],
                "message_body": "Pay ₹300 for Costume Hire",
                "actor_name": "Father",
            },
        )
        assert res_rem.status_code == 201

        # 6. Assistant Rejected (403)
        res_asst = client.post(
            f"/api/actions/{act_id}/approve",
            json={"expected_version": 2, "actor_type": "assistant", "actor_name": "AI Assistant"},
        )
        assert res_asst.status_code == 403

        # 7. Parent Approve & Complete
        res_parent = client.post(
            f"/api/actions/{act_id}/approve",
            json={"expected_version": 2, "actor_type": "parent", "actor_name": "Father"},
        )
        assert res_parent.status_code == 200
        assert res_parent.json()["version"] == 3

        res_comp = client.post(
            f"/api/actions/{act_id}/complete",
            json={"expected_version": 3, "actor_type": "parent", "actor_name": "Father"},
        )
        assert res_comp.status_code == 200
        assert res_comp.json()["status"] == "completed"

        # 8. Full readback
        res_read = client.get(f"/api/notices/{notice_id}")
        assert res_read.status_code == 200
        agg = res_read.json()
        assert len(agg["actions"]) >= 2
        assert len(agg["reminders"]) == 1
        assert len(agg["audit_events"]) >= 3


def test_concurrent_optimistic_conflict_postgres(
    pg_cluster: DisposablePostgresCluster | None,
) -> None:
    """Two concurrent client mutations against the same action yield exactly 1 success and 1 conflict."""
    if pg_cluster is None:
        pytest.skip("Local PostgreSQL 16.10 binaries not available")

    db_url = pg_cluster.create_isolated_db("sb_conflict")
    app = create_app(db_url)

    with TestClient(app) as setup_client:
        setup_client.post("/api/workspaces")
        token = setup_client.cookies["schoolbag_session"]
        res = setup_client.post(
            "/api/notices",
            json={
                "source_type": "whatsapp",
                "class_name": "Class 5-B",
                "child_alias": "Kavya",
                "title": "Concurrence Notice",
                "raw_body": "Fee due ₹100",
            },
        )
        action_id = res.json()["actions"][0]["action_id"]

    results: list[int] = []

    def _worker(thread_id: int) -> None:
        with TestClient(app) as client:
            client.cookies.set("schoolbag_session", token)
            res_patch = client.patch(
                f"/api/actions/{action_id}/deadline",
                json={
                    "expected_version": 1,
                    "raw_deadline": f"Deadline from thread {thread_id}",
                    "actor_name": f"Parent {thread_id}",
                },
            )
            results.append(res_patch.status_code)

    t1 = threading.Thread(target=_worker, args=(1,))
    t2 = threading.Thread(target=_worker, args=(2,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exactly one must succeed (200) and one must fail with optimistic conflict (409)
    assert 200 in results
    assert 409 in results
