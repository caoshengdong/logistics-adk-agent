"""Backend configuration — loaded once from environment / .env."""

from __future__ import annotations

import os
from pathlib import Path

import dotenv

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _BACKEND_ROOT.parent
# .env lives at project root (for docker-compose); fall back to backend/ for local dev
dotenv.load_dotenv(_PROJECT_ROOT / ".env")
dotenv.load_dotenv(_BACKEND_ROOT / ".env")


def _normalize_database_url(url: str) -> str:
    """Ensure the DATABASE_URL uses the asyncpg driver.

    Hosted providers (Render, Heroku, etc.) typically supply a URL starting
    with ``postgres://`` or ``postgresql://``.  SQLAlchemy async requires
    ``postgresql+asyncpg://``.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class BackendSettings:
    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24h

    # Database — PostgreSQL (async via asyncpg)
    database_url: str = _normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/logistics",
        )
    )

    # CORS — in production, set to the frontend's public URL
    # e.g. "https://logistics.onrender.com,https://custom-domain.com"
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ]

    # ADK
    adk_app_name: str = "logistics"


backend_settings = BackendSettings()

