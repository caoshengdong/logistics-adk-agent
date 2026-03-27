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
    api_base_url: str | None = os.getenv("LOGISTICS_API_BASE_URL")
    api_key: str | None = os.getenv("LOGISTICS_API_KEY")
    http_timeout_seconds: float = float(os.getenv("LOGISTICS_HTTP_TIMEOUT_SECONDS", "10"))
    default_origin_country: str = "CN"
    default_destination_country: str = "US"


settings = Settings()
