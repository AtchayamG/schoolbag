"""Tests for full-stack packaging, health/readiness probes, and strict JSON 404."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

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


def test_health_and_readiness_probes(client: TestClient) -> None:
    """Verify health and readiness endpoints disclose truthful status and engine."""
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    h = res_health.json()
    assert h["status"] == "ok"
    assert h["app"] == "Schoolbag"
    assert h["database"]["engine"] == "sqlite"
    assert h["extractor"]["mode"] == "deterministic"

    res_ready = client.get("/api/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"


def test_strict_json_404_for_unknown_api_endpoints(client: TestClient) -> None:
    """Unknown endpoints under /api/* must return standard JSON 404 envelope across all HTTP methods."""
    methods = ["get", "post", "put", "patch", "delete"]
    unknown_routes = [
        "/api/unknown",
        "/api/notices/123/nonexistent",
        "/api/actions/xyz/fake_action",
    ]

    for route in unknown_routes:
        for m in methods:
            fn = getattr(client, m)
            res = fn(route)
            assert res.status_code == 404, f"Expected 404 for {m.upper()} {route}"
            assert res.headers["content-type"].startswith("application/json")
            data = res.json()
            assert data["error"] == "NOT_FOUND"
            assert "does not exist" in data["message"]


def test_spa_static_serving_and_fallback(tmp_path: Path) -> None:
    """FastAPI serves built static assets and falls back to index.html for SPA client routes."""
    # Create fake built dist directory
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html><body>Schoolbag SPA</body></html>", encoding="utf-8")
    (dist / "main.js").write_text("console.log('spa');", encoding="utf-8")

    import os

    os.environ["SCHOOLBAG_STATIC_DIR"] = str(dist)
    try:
        app = create_app(f"sqlite:///{tmp_path / 'app.db'}")
        with TestClient(app) as spa_client:
            # Root route serves index.html
            res_root = spa_client.get("/")
            assert res_root.status_code == 200
            assert "Schoolbag SPA" in res_root.text

            # Static asset serves file directly
            res_js = spa_client.get("/main.js")
            assert res_js.status_code == 200
            assert "console.log('spa');" in res_js.text

            # SPA client route (e.g. /notices/view) falls back to index.html
            res_client_route = spa_client.get("/notices/view")
            assert res_client_route.status_code == 200
            assert "Schoolbag SPA" in res_client_route.text
    finally:
        os.environ.pop("SCHOOLBAG_STATIC_DIR", None)
