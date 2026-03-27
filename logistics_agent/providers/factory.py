from __future__ import annotations

from functools import lru_cache

from logistics_agent.config import settings
from logistics_agent.providers.base import LogisticsProvider
from logistics_agent.providers.http_provider import HttpLogisticsProvider
from logistics_agent.providers.mock_provider import MockLogisticsProvider


@lru_cache(maxsize=1)
def get_provider() -> LogisticsProvider:
    if settings.provider_backend == "http":
        if not settings.api_base_url or not settings.api_key:
            raise ValueError(
                "LOGISTICS_PROVIDER_BACKEND=http requires LOGISTICS_API_BASE_URL and LOGISTICS_API_KEY"
            )
        return HttpLogisticsProvider(
            base_url=settings.api_base_url,
            api_key=settings.api_key,
            timeout_seconds=settings.http_timeout_seconds,
        )
    return MockLogisticsProvider()
