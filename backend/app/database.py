"""SQLAlchemy async engine + session factory (PostgreSQL / asyncpg)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import backend_settings

engine = create_async_engine(
    backend_settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency — yields a DB session per request."""
    async with async_session_factory() as session:
        yield session
