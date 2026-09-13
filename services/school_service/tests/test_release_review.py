from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from schoolbag.config import get_settings
from schoolbag.interfaces.http.app import create_app


def test_missing_or_unrecognized_deadlines_are_not_invented() -> None:
    from schoolbag.infrastructure.extractor import DeterministicActionExtractor
    from schoolbag.infrastructure.normalizer import normalize_deadline

    assert normalize_deadline("Ask the class teacher") is None
    actions, _ = DeterministicActionExtractor().extract_actions(
        "Activity fee", "Please pay Rs 350 and return consent", None, "Kavya", "5-B"
    )
    assert actions
    assert all(action["normalized_deadline"] is None for action in actions)


def test_production_page_can_bootstrap_without_session(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    static = tmp_path / "web"
    static.mkdir()
    (static / "index.html").write_text("Schoolbag public page")
    monkeypatch.setenv("SCHOOLBAG_STATIC_DIR", str(static))
    monkeypatch.setenv("SCHOOLBAG_ENVIRONMENT", "production")
    monkeypatch.setenv("SCHOOLBAG_CORS_ORIGINS", "https://schoolbag.example")
    get_settings.cache_clear()
    try:
        with TestClient(create_app(f"sqlite:///{tmp_path / 'test.db'}")) as client:
            assert client.get("/").status_code == 200
            assert client.get("/api/notices").status_code != 200
            assert client.get("/api/ready").status_code == 200
    finally:
        get_settings.cache_clear()


def test_readiness_accepts_postgres_dictionary_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from contextlib import contextmanager

    class Connection:
        def cursor(self):
            return self

        def execute(self, sql):
            assert sql == "SELECT 1 AS ready"

        def fetchone(self):
            return {"ready": 1}

    @contextmanager
    def connection():
        yield Connection()

    app = create_app(f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setattr(app.state.store, "_get_connection", connection)
    with TestClient(app) as client:
        assert client.get("/api/ready").status_code == 200
