from __future__ import annotations

from functools import lru_cache

from logistics_agent.config import settings
from logistics_agent.providers.base import LogisticsProvider
from logistics_agent.providers.http_provider import HttpLogisticsProvider
from logistics_agent.providers.mock_provider import MockLogisticsProvider


@lru_cache(maxsize=1)
def get_provider() -> LogisticsProvider:
    if settings.provider_backend == "http":
        if not settings.auth_code or not settings.auth_token:
            raise ValueError(
                "LOGISTICS_PROVIDER_BACKEND=http requires LOGISTICS_AUTH_CODE and LOGISTICS_AUTH_TOKEN"
            )
        return HttpLogisticsProvider(
            base_url=settings.api_base_url,
            auth_code=settings.auth_code,
            auth_token=settings.auth_token,
            timeout_seconds=settings.http_timeout_seconds,
        )
    return MockLogisticsProvider()
