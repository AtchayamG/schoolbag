"""Session and workspace management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response

from schoolbag.domain.models import Workspace
from schoolbag.domain.ports import SchoolbagStorePort
from schoolbag.infrastructure.session import (
    DEFAULT_WORKSPACE_ID,
    SESSION_COOKIE_NAME,
    generate_session_token,
    resolve_session_token,
)
from schoolbag.interfaces.http.schemas import WorkspaceResponse

router = APIRouter(prefix="/api/workspaces", tags=["Session & Workspaces"])


def get_current_workspace(request: Request) -> Workspace:
    """Dependency to resolve current active workspace from session token."""
    store: SchoolbagStorePort = request.app.state.store
    token = resolve_session_token(request)
    if not token:
        # Check if running in test/dev with fallback
        if not getattr(request.app.state, "is_production", False):
            token = f"dev_session_{DEFAULT_WORKSPACE_ID}"
        else:
            token = generate_session_token()
    ws = store.get_or_create_workspace(token)
    return ws


@router.post("", response_model=WorkspaceResponse)
def initialize_workspace(request: Request, response: Response) -> WorkspaceResponse:
    """Initialize or touch public workbench session and set HttpOnly cookie."""
    store: SchoolbagStorePort = request.app.state.store
    token = resolve_session_token(request)
    is_new = False
    if not token:
        token = generate_session_token()
        is_new = True

    ws = store.get_or_create_workspace(token)

    # Set HttpOnly, SameSite=Lax cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=30 * 86400,
        httponly=True,
        samesite="lax",
        secure=getattr(request.app.state, "is_production", False),
        path="/",
    )
    return WorkspaceResponse(
        workspace_id=ws.workspace_id,
        session_token=ws.session_token if is_new else f"{ws.session_token[:8]}...",
        notice_count=ws.notice_count,
        capacity_limit=50,
        is_active=ws.is_active,
        created_at=ws.created_at,
        updated_at=ws.updated_at,
        expires_at=ws.expires_at,
    )


@router.get("/current", response_model=WorkspaceResponse)
def get_current_workspace_info(ws: Workspace = Depends(get_current_workspace)) -> WorkspaceResponse:
    """Get active workspace status, token prefix, and notice capacity count."""
    return WorkspaceResponse(
        workspace_id=ws.workspace_id,
        session_token=f"{ws.session_token[:8]}...",
        notice_count=ws.notice_count,
        capacity_limit=50,
        is_active=ws.is_active,
        created_at=ws.created_at,
        updated_at=ws.updated_at,
        expires_at=ws.expires_at,
    )
