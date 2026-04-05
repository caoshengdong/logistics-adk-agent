"""Shared service helpers for all tool modules.

- ``get_service()`` — backward-compatible global singleton (env-level creds).
- ``get_service_for_user(auth_code, auth_token)`` — per-user cached instance.
- ``resolve_service(tool_context)`` — pick the right service from ToolContext.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from logistics_agent.providers.factory import get_provider, get_provider_for_user
from logistics_agent.services.logistics_service import LogisticsService

if TYPE_CHECKING:
    from google.adk.tools import ToolContext


@lru_cache(maxsize=1)
def get_service() -> LogisticsService:
    """Global service using env-level credentials (backward compatible)."""
    return LogisticsService(provider=get_provider())


@lru_cache(maxsize=64)
def get_service_for_user(auth_code: str, auth_token: str) -> LogisticsService:
    """Per-user service cached by (auth_code, auth_token)."""
    provider = get_provider_for_user(auth_code, auth_token)
    return LogisticsService(provider=provider)


def resolve_service(tool_context: ToolContext | None = None) -> LogisticsService:
    """Pick the right LogisticsService based on ToolContext session state.

    If the ADK session carries ``auth_code`` / ``auth_token`` in its state,
    a per-user service is returned; otherwise the global singleton is used.
    """
    if tool_context is not None:
        auth_code = (tool_context.state or {}).get("auth_code", "")
        auth_token = (tool_context.state or {}).get("auth_token", "")
        if auth_code and auth_token:
            return get_service_for_user(auth_code, auth_token)
    return get_service()


