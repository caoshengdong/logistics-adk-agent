from __future__ import annotations

from functools import lru_cache

from agent.config import settings
from agent.providers.base import LogisticsProvider
from agent.providers.http_provider import HttpLogisticsProvider
from agent.providers.mock_provider import MockLogisticsProvider


@lru_cache(maxsize=1)
def get_provider() -> LogisticsProvider:
    """Global provider using env-level credentials (backward compatible)."""
    if settings.provider_backend == "http":
        if not settings.auth_code or not settings.auth_token:
            raise ValueError(
                "LOGISTICS_PROVIDER_BACKEND=http requires "
                "LOGISTICS_AUTH_CODE and LOGISTICS_AUTH_TOKEN"
            )
        return HttpLogisticsProvider(
            base_url=settings.api_base_url,
            auth_code=settings.auth_code,
            auth_token=settings.auth_token,
            timeout_seconds=settings.http_timeout_seconds,
        )
    return MockLogisticsProvider()


@lru_cache(maxsize=64)
def get_provider_for_user(auth_code: str, auth_token: str) -> LogisticsProvider:
    """Per-user provider cached by (auth_code, auth_token) tuple.

    If the backend is ``http`` and both credentials are provided, returns an
    ``HttpLogisticsProvider`` bound to that specific customer.  Otherwise
    falls back to the global provider (respecting the ``provider_backend``
    setting).
    """
    if settings.provider_backend == "http" and auth_code and auth_token:
        return HttpLogisticsProvider(
            base_url=settings.api_base_url,
            auth_code=auth_code,
            auth_token=auth_token,
            timeout_seconds=settings.http_timeout_seconds,
        )
    return get_provider()

