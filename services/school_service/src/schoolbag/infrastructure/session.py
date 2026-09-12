"""Session and workspace token management with production boundary enforcement."""

from __future__ import annotations

import secrets
from urllib.parse import urlparse

from fastapi import Request

from schoolbag.config import is_production_environment
from schoolbag.domain.errors import OriginRefusedError, SessionExpiredError

SESSION_COOKIE_NAME = "schoolbag_session"
DEFAULT_WORKSPACE_ID = "legacy_local_workspace"


def generate_session_token() -> str:
    """Generate cryptographically secure 32-byte (64 hex chars) opaque session token."""
    return secrets.token_hex(32)


def resolve_session_token(request: Request) -> str | None:
    """Resolve session token from HttpOnly cookie or headers."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token and token.strip():
        return token.strip()

    header_token = request.headers.get("X-Schoolbag-Session")
    if header_token and header_token.strip():
        return header_token.strip()

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        bearer = auth_header[7:].strip()
        if bearer:
            return bearer

    return None


def validate_production_request(
    request: Request,
    allowed_origins: list[str],
    environment: str | None = None,
) -> None:
    """Enforce production security: validate Origin header and require active session cookie."""
    if not is_production_environment(environment):
        return

    # Check origin for state-modifying HTTP methods
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("origin")
        if not origin:
            raise OriginRefusedError("Missing Origin header in production mutation request.")

        if "*" not in allowed_origins:
            parsed = urlparse(origin)
            origin_clean = f"{parsed.scheme}://{parsed.netloc}"
            if origin_clean not in allowed_origins and origin not in allowed_origins:
                raise OriginRefusedError(f"Origin '{origin}' is not permitted by security policy.")

    # Require session cookie in production
    token = resolve_session_token(request)
    if not token:
        raise SessionExpiredError("Session cookie missing or expired in production environment.")
