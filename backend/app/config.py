"""Backend configuration — loaded once from environment / .env."""

from __future__ import annotations

import os
from pathlib import Path

import dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
dotenv.load_dotenv(_PROJECT_ROOT / ".env")


class BackendSettings:
    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24h

    # Database — SQLite by default, swap to PostgreSQL for production
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{_PROJECT_ROOT / 'backend' / 'data' / 'logistics.db'}",
    )

    # CORS
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")

    # ADK
    adk_app_name: str = "logistics"


backend_settings = BackendSettings()

