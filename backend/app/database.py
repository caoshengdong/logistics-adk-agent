"""SQLAlchemy async engine + session factory."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.config import backend_settings

# Ensure the data directory exists for SQLite
_db_url = backend_settings.database_url
if _db_url.startswith("sqlite"):
    _db_path = _db_url.split("///")[-1]
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(_db_url, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency — yields a DB session per request."""
    async with async_session_factory() as session:
        yield session

