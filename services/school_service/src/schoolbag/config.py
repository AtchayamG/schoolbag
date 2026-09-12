"""Schoolbag configuration and environment management."""

from __future__ import annotations

import json
import os
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PRODUCTION_ALIASES = {"production", "prod"}


def is_production_environment(env: str | None = None) -> bool:
    """Determine if given or configured environment is production."""
    if env is None:
        env = os.environ.get("SCHOOLBAG_ENVIRONMENT", os.environ.get("ENVIRONMENT", "development"))
    return env.strip().lower() in _PRODUCTION_ALIASES


class SchoolbagSettings(BaseSettings):
    """Runtime application settings for Schoolbag."""

    model_config = SettingsConfigDict(
        env_prefix="SCHOOLBAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(
        default_factory=lambda: os.environ.get(
            "SCHOOLBAG_ENVIRONMENT", os.environ.get("ENVIRONMENT", "development")
        ),
        description="Runtime environment",
    )
    database_url: str = Field(
        default_factory=lambda: os.environ.get(
            "SCHOOLBAG_DATABASE_URL", os.environ.get("DATABASE_URL", "sqlite:///schoolbag.db")
        ),
        description="Database connection URL",
    )
    cors_origins: str = Field(
        default_factory=lambda: os.environ.get(
            "SCHOOLBAG_CORS_ORIGINS",
            os.environ.get("CORS_ORIGINS", "http://localhost:5174,http://127.0.0.1:5174"),
        ),
        description="Allowed CORS origins (comma-separated or JSON list)",
    )
    static_dir: str = Field(
        default="apps/web/dist", description="Path to built static frontend assets"
    )
    port: int = Field(default=8002, description="HTTP listen port")
    host: str = Field(default="0.0.0.0", description="HTTP listen host")
    session_ttl_seconds: int = Field(default=30 * 86400, description="Session TTL (30 days)")
    workspace_notice_limit: int = Field(default=50, description="Max notices per workspace")
    global_workspace_limit: int = Field(default=1000, description="Global active workspaces limit")
    extraction_mode: str = Field(default="deterministic", description="Extraction engine mode")

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Normalize postgres:// to postgresql:// for psycopg compatibility."""
        if v.startswith("postgres://"):
            return "postgresql://" + v[len("postgres://") :]
        return v

    @property
    def is_production(self) -> bool:
        """Check if environment is production."""
        return is_production_environment(self.environment)

    def parse_cors_origins(self) -> list[str]:
        """Parse CORS origins string into list of origin URLs."""
        val = self.cors_origins.strip()
        if not val or val == "*":
            return ["*"]
        if val.startswith("[") and val.endswith("]"):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in val.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> SchoolbagSettings:
    """Retrieve cached application settings singleton."""
    return SchoolbagSettings()
