"""PostgreSQL-backed ADK ArtifactService.

Replaces ``InMemoryArtifactService`` so that artifacts (e.g. PDF quotations)
are persisted across server restarts.  Uses synchronous SQLAlchemy sessions
internally because ADK's ``BaseArtifactService`` methods are ``async`` but
the underlying tool calls run within the agent's synchronous context in
practice, and we need a self-contained DB session (the FastAPI request-scoped
session is not available inside the ADK runner).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from google.adk.artifacts.base_artifact_service import (
    ArtifactVersion,
    BaseArtifactService,
    ensure_part,
)
from google.genai import types
from sqlalchemy import create_engine, select
from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import Session

from app.config import backend_settings
from app.models import Artifact

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level lazy engine (shared by DBArtifactService and save_artifact_to_db)
# ---------------------------------------------------------------------------
_module_engine = None


def _get_module_engine():
    """Return (and lazily create) a module-level sync engine."""
    global _module_engine
    if _module_engine is None:
        _module_engine = create_engine(
            _sync_database_url(),
            pool_size=3,
            max_overflow=5,
        )
    return _module_engine


def save_artifact_to_db(
    *,
    session_id: str,
    user_id: str,
    filename: str,
    data: bytes,
    content_type: str = "application/pdf",
) -> tuple[str, int]:
    """Save artifact directly to PostgreSQL, bypassing ADK's Part flow.

    This avoids the ``copy.deepcopy`` error that occurs when ADK tries to
    deepcopy a ``types.Part`` containing binary data (PDF).

    Returns ``(artifact_id, version)``.
    """
    engine = _get_module_engine()
    with Session(engine) as db:
        existing = db.execute(
            select(Artifact.version)
            .where(
                Artifact.session_id == session_id,
                Artifact.filename == filename,
            )
            .order_by(Artifact.version.desc())
        ).scalars().first()

        version = 0 if existing is None else existing + 1

        row_id = _new_uuid()
        row = Artifact(
            id=row_id,
            session_id=session_id,
            user_id=user_id,
            filename=filename,
            version=version,
            content_type=content_type,
            data=data,
        )
        db.add(row)
        db.commit()

        logger.info(
            "Saved artifact %s v%d (%d bytes, id=%s) for session %s",
            filename, version, len(data), row_id, session_id,
        )
        return row_id, version


def _sync_database_url() -> str:
    """Convert the async database URL to a sync one using psycopg (psycopg3)."""
    url = backend_settings.database_url
    # asyncpg URL: postgresql+asyncpg://... → psycopg URL: postgresql+psycopg://...
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return uuid.uuid4().hex


class DBArtifactService(BaseArtifactService):
    """ADK ArtifactService backed by PostgreSQL ``artifacts`` table.

    Each artifact version is a row in the DB.  The ``(session_id, filename,
    version)`` triple uniquely identifies a blob.

    This service creates its own synchronous SQLAlchemy engine (lazily) so it
    is fully self-contained and does not depend on FastAPI's request-scoped
    async session.
    """

    def __init__(self) -> None:
        super().__init__()

    def _get_session(self) -> Session:
        return Session(_get_module_engine())

    # ------------------------------------------------------------------
    # save_artifact
    # ------------------------------------------------------------------

    async def save_artifact(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        artifact: types.Part | dict[str, Any],
        session_id: str | None = None,
        custom_metadata: dict[str, Any] | None = None,
    ) -> int:
        artifact = ensure_part(artifact)

        if session_id is None:
            raise ValueError("session_id is required for DBArtifactService")

        # Extract binary data
        if artifact.inline_data is not None:
            data_bytes = artifact.inline_data.data or b""
            mime_type = artifact.inline_data.mime_type or "application/octet-stream"
        elif artifact.text is not None:
            data_bytes = artifact.text.encode("utf-8")
            mime_type = "text/plain"
        else:
            raise ValueError("Unsupported artifact type — only inline_data and text are supported")

        with self._get_session() as db:
            # Determine next version number
            existing_count = db.execute(
                select(Artifact.version)
                .where(
                    Artifact.session_id == session_id,
                    Artifact.filename == filename,
                )
                .order_by(Artifact.version.desc())
            ).scalars().first()

            version = 0 if existing_count is None else existing_count + 1

            row = Artifact(
                id=_new_uuid(),
                session_id=session_id,
                user_id=user_id,
                filename=filename,
                version=version,
                content_type=mime_type,
                data=data_bytes,
            )
            db.add(row)
            db.commit()

            logger.info(
                "Saved artifact %s v%d (%d bytes) for session %s",
                filename, version, len(data_bytes), session_id,
            )
            return version

    # ------------------------------------------------------------------
    # load_artifact
    # ------------------------------------------------------------------

    async def load_artifact(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        session_id: str | None = None,
        version: int | None = None,
    ) -> types.Part | None:
        if session_id is None:
            return None

        with self._get_session() as db:
            query = (
                select(Artifact)
                .where(
                    Artifact.session_id == session_id,
                    Artifact.filename == filename,
                )
            )
            if version is not None:
                query = query.where(Artifact.version == version)
            else:
                query = query.order_by(Artifact.version.desc())

            row = db.execute(query).scalars().first()
            if row is None:
                return None

            return types.Part.from_bytes(
                data=row.data,
                mime_type=row.content_type,
            )

    # ------------------------------------------------------------------
    # list_artifact_keys
    # ------------------------------------------------------------------

    async def list_artifact_keys(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str | None = None,
    ) -> list[str]:
        with self._get_session() as db:
            query = select(Artifact.filename).distinct()
            if session_id:
                query = query.where(Artifact.session_id == session_id)
            else:
                query = query.where(Artifact.user_id == user_id)
            rows = db.execute(query).scalars().all()
            return sorted(rows)

    # ------------------------------------------------------------------
    # delete_artifact
    # ------------------------------------------------------------------

    async def delete_artifact(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        session_id: str | None = None,
    ) -> None:
        with self._get_session() as db:
            stmt = sa_delete(Artifact).where(
                Artifact.filename == filename,
                Artifact.user_id == user_id,
            )
            if session_id:
                stmt = stmt.where(Artifact.session_id == session_id)
            db.execute(stmt)
            db.commit()

    # ------------------------------------------------------------------
    # list_versions
    # ------------------------------------------------------------------

    async def list_versions(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        session_id: str | None = None,
    ) -> list[int]:
        with self._get_session() as db:
            query = (
                select(Artifact.version)
                .where(Artifact.filename == filename)
                .order_by(Artifact.version)
            )
            if session_id:
                query = query.where(Artifact.session_id == session_id)
            else:
                query = query.where(Artifact.user_id == user_id)
            return list(db.execute(query).scalars().all())

    # ------------------------------------------------------------------
    # list_artifact_versions
    # ------------------------------------------------------------------

    async def list_artifact_versions(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        session_id: str | None = None,
    ) -> list[ArtifactVersion]:
        with self._get_session() as db:
            query = (
                select(Artifact)
                .where(Artifact.filename == filename)
                .order_by(Artifact.version)
            )
            if session_id:
                query = query.where(Artifact.session_id == session_id)
            else:
                query = query.where(Artifact.user_id == user_id)

            rows = db.execute(query).scalars().all()
            return [
                ArtifactVersion(
                    version=row.version,
                    canonical_uri=f"db://artifacts/{row.id}",
                    mime_type=row.content_type,
                    create_time=row.created_at.timestamp() if row.created_at else 0,
                )
                for row in rows
            ]

    # ------------------------------------------------------------------
    # get_artifact_version
    # ------------------------------------------------------------------

    async def get_artifact_version(
        self,
        *,
        app_name: str,
        user_id: str,
        filename: str,
        session_id: str | None = None,
        version: int | None = None,
    ) -> ArtifactVersion | None:
        with self._get_session() as db:
            query = select(Artifact).where(Artifact.filename == filename)
            if session_id:
                query = query.where(Artifact.session_id == session_id)
            else:
                query = query.where(Artifact.user_id == user_id)

            if version is not None:
                query = query.where(Artifact.version == version)
            else:
                query = query.order_by(Artifact.version.desc())

            row = db.execute(query).scalars().first()
            if row is None:
                return None

            return ArtifactVersion(
                version=row.version,
                canonical_uri=f"db://artifacts/{row.id}",
                mime_type=row.content_type,
                create_time=row.created_at.timestamp() if row.created_at else 0,
            )

