"""FastAPI application factory, middleware, exception handlers, and SPA static serving."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from schoolbag.config import get_settings
from schoolbag.domain.errors import SchoolbagDomainError
from schoolbag.infrastructure.admission import InferenceAdmissionStore
from schoolbag.infrastructure.extractor import DeterministicActionExtractor
from schoolbag.infrastructure.session import validate_production_request
from schoolbag.infrastructure.sqlite_store import SqliteSchoolbagStore
from schoolbag.infrastructure.strands_agent import StrandsAdvisoryEngine
from schoolbag.interfaces.http.routes.actions import router as actions_router
from schoolbag.interfaces.http.routes.notices import router as notices_router
from schoolbag.interfaces.http.routes.reminders import router as reminders_router
from schoolbag.interfaces.http.routes.session import router as session_router


class SecurityMiddleware(BaseHTTPMiddleware):
    """Enforces production Origin validation and session cookie checks."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        # Skip health, readiness, and docs endpoints
        path = request.url.path
        if not path.startswith("/api/") or path in ("/api/health", "/api/ready"):
            return await call_next(request)  # type: ignore[no-any-return]

        settings = get_settings()
        allowed_origins = settings.parse_cors_origins()

        try:
            validate_production_request(request, allowed_origins, settings.environment)
        except SchoolbagDomainError as exc:
            error_res = JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.code, "message": exc.message, "details": exc.details},
            )
            error_res.headers["X-Content-Type-Options"] = "nosniff"
            error_res.headers["X-Frame-Options"] = "DENY"
            error_res.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            return error_res

        res = await call_next(request)
        res.headers["X-Content-Type-Options"] = "nosniff"
        res.headers["X-Frame-Options"] = "DENY"
        res.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return res  # type: ignore[no-any-return]


def create_app(
    db_url: str | None = None,
    extraction_mode: str | None = None,
    raw_conn_factory: Callable[[], Any] | None = None,
    admission_store: InferenceAdmissionStore | None = None,
    strands_engine: StrandsAdvisoryEngine | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """Create and configure the Schoolbag FastAPI application."""
    settings = get_settings()
    target_db = db_url or settings.database_url
    target_mode = extraction_mode or settings.extraction_mode

    is_postgres = target_db.startswith("postgresql://") or target_db.startswith("postgres://")
    if settings.is_production:
        origins = settings.parse_cors_origins()
        if not origins or any(not origin.startswith("https://") for origin in origins):
            raise ValueError("Production requires explicit HTTPS origins")
        if db_url is None and not is_postgres:
            raise ValueError("Production requires a persistent PostgreSQL database")
        if target_mode not in {"live", "deterministic"}:
            raise ValueError("Unsupported production extraction mode")

    app = FastAPI(
        title="Schoolbag",
        description="Turns scattered school notices into the few things a family actually needs to do",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Initialize store and extractor on app state
    clean_db_path = target_db
    if clean_db_path.startswith("sqlite:///"):
        clean_db_path = clean_db_path[len("sqlite:///") :]

    app.state.store = SqliteSchoolbagStore(
        db_path=clean_db_path,
        is_postgres=is_postgres,
        raw_conn_factory=raw_conn_factory,
    )
    app.state.extractor = DeterministicActionExtractor(mode=target_mode)
    app.state.extraction_mode = target_mode
    app.state.is_production = settings.is_production

    # Initialize admission store and Strands advisory engine
    app.state.admission_store = admission_store or InferenceAdmissionStore(
        target_db if is_postgres else f"sqlite:///{clean_db_path}"
    )
    app.state.strands_engine = strands_engine or StrandsAdvisoryEngine(
        admission_store=app.state.admission_store,
        api_key=os.environ.get("GROQ_API_KEY"),
        transport=transport,
        mode=target_mode,
    )

    # Middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.parse_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityMiddleware)

    # Include routers
    app.include_router(session_router)
    app.include_router(notices_router)
    app.include_router(actions_router)
    app.include_router(reminders_router)

    # Exception handlers
    @app.exception_handler(SchoolbagDomainError)
    async def domain_error_handler(_request: Request, exc: SchoolbagDomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request payload validation failed.",
                "details": {"errors": exc.errors()},
            },
        )

    @app.get("/api/health")
    def health_check() -> JSONResponse:
        """Health check endpoint disclosing engine provenance and mode."""
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "app": "Schoolbag",
                "version": "0.1.0",
                "milestone": "M1",
                "extractor": {
                    "mode": app.state.extraction_mode,
                    "status": "operational",
                    "advisory_only": True,
                },
                "strands": {
                    "engine": "strands",
                    "status": "configured" if app.state.strands_engine._api_key else "unavailable",
                    "live_verified": False,
                    "advisory_only": True,
                },
                "database": {
                    "engine": "postgres" if app.state.store.is_postgres else "sqlite",
                    "status": "connected",
                },
            },
        )

    @app.get("/api/ready")
    def readiness_check() -> Response:
        """Readiness probe checking database responsiveness."""
        try:
            with app.state.store._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1 AS ready")
                row = cur.fetchone()
                if row and (row["ready"] if isinstance(row, dict) else row[0]) == 1:
                    return JSONResponse(
                        status_code=200, content={"status": "ready", "database": "connected"}
                    )
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "error": "Database readiness check failed"},
            )
        return JSONResponse(status_code=503, content={"status": "not_ready"})

    # Strict JSON 404 handler for unknown API routes
    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def api_404_handler(request: Request, path: str) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "NOT_FOUND",
                "message": f"API endpoint '/api/{path}' does not exist.",
                "details": {},
            },
        )

    # Static frontend assets and SPA fallback
    static_path_str = os.environ.get("SCHOOLBAG_STATIC_DIR", settings.static_dir)
    static_dir = Path(static_path_str).resolve()
    if static_dir.exists() and (static_dir / "index.html").exists():
        index_file = static_dir / "index.html"

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str) -> Response:
            if full_path.startswith("api"):
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": "NOT_FOUND",
                        "message": f"Endpoint '/{full_path}' not found.",
                    },
                )
            target = (static_dir / full_path).resolve()
            if not target.is_relative_to(static_dir):
                return JSONResponse(status_code=404, content={"error": "NOT_FOUND"})
            if target.exists() and target.is_file():
                return FileResponse(str(target))
            return FileResponse(str(index_file))

    return app
