"""Shared singleton for all tool modules."""

from __future__ import annotations

from functools import lru_cache

from logistics_agent.providers.factory import get_provider
from logistics_agent.services.logistics_service import LogisticsService


@lru_cache(maxsize=1)
def get_service() -> LogisticsService:
    return LogisticsService(provider=get_provider())

