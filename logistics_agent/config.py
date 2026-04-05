from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    model: str = os.getenv("LOGISTICS_AGENT_MODEL", "gemini-3-flash-preview")
    provider_backend: str = os.getenv("LOGISTICS_PROVIDER_BACKEND", "mock")
    api_base_url: str = os.getenv("LOGISTICS_API_BASE_URL", "http://47.115.60.18")
    auth_code: str | None = os.getenv("LOGISTICS_AUTH_CODE")
    auth_token: str | None = os.getenv("LOGISTICS_AUTH_TOKEN")
    http_timeout_seconds: float = float(os.getenv("LOGISTICS_HTTP_TIMEOUT_SECONDS", "10"))


settings = Settings()
