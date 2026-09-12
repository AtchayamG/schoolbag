"""Tests for configuration, production CORS/Origin security, and presets."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from schoolbag.config import get_settings, is_production_environment
from schoolbag.infrastructure.seed_data import PRESET_NOTICES, get_preset_by_id
from schoolbag.interfaces.http.app import create_app


def test_production_environment_detector() -> None:
    """Detects various production string representations."""
    assert is_production_environment("production") is True
    assert is_production_environment("Production") is True
    assert is_production_environment("prod") is True
    assert is_production_environment("PROD") is True
    assert is_production_environment("development") is False
    assert is_production_environment("test") is False


def test_security_response_headers(tmp_path: Path) -> None:
    """All API responses enforce strict nosniff, DENY frame, and referrer policy."""
    app = create_app(f"sqlite:///{tmp_path / 'sec.db'}")
    with TestClient(app) as client:
        res = client.post("/api/workspaces", json={"name": "Test Sec"})
        assert res.status_code == 200
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert res.headers.get("X-Frame-Options") == "DENY"
        assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_production_origin_enforcement(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Production mode rejects requests from unlisted external origins with 403."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv(
        "SCHOOLBAG_CORS_ORIGINS", "https://schoolbag.onrender.com,https://schoolbag.vercel.app"
    )
    get_settings.cache_clear()

    try:
        app = create_app(f"sqlite:///{tmp_path / 'prod.db'}")
        with TestClient(app) as client:
            # Request with untrusted origin -> 403 ORIGIN_REFUSED
            res_bad = client.post(
                "/api/workspaces",
                json={"name": "Attacker"},
                headers={"Origin": "https://malicious-phishing.com"},
            )
            assert res_bad.status_code == 403
            assert res_bad.json()["error"] == "ORIGIN_REFUSED"
            assert res_bad.headers.get("X-Frame-Options") == "DENY"

            # Request with trusted origin -> 200 OK
            res_good = client.post(
                "/api/workspaces",
                json={"name": "Valid Tenant"},
                headers={"Origin": "https://schoolbag.vercel.app"},
            )
            assert res_good.status_code == 200
    finally:
        get_settings.cache_clear()


def test_preset_catalog_integrity() -> None:
    """Presets cover believable Kovai Vidya Mandir, Coimbatore scenarios."""
    assert len(PRESET_NOTICES) >= 4
    preset_ids = [p["preset_id"] for p in PRESET_NOTICES]
    assert "preset-science-kit" in preset_ids
    assert "preset-annual-day" in preset_ids
    assert "preset-term-exam" in preset_ids
    assert "preset-sports-day" in preset_ids

    # Every preset has required fields and minimal alias only
    for p in PRESET_NOTICES:
        assert p["child_alias"] in ("Kavya", "Arun")
        assert "Class" in p["class_name"]
        assert (
            "Coimbatore" in p["raw_body"]
            or "Kovai" in p["raw_body"]
            or "Principal" in p["raw_body"]
            or "School" in p["raw_body"]
        )
        assert get_preset_by_id(p["preset_id"]) is not None

    assert get_preset_by_id("non-existent") is None
