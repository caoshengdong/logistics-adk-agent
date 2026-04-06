"""Chat routes: SSE streaming, sessions CRUD, message history."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.auth.dependencies import get_current_user
from app.chat.adk_runner import delete_adk_session, run_agent_stream
from app.database import get_db
from app.models import Artifact, ChatMessage, ChatSession, User
from app.schemas import (
    ChatRequest,
    ChatSessionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


# ── SSE streaming chat ───────────────────────────────────────────────────

@router.post("")
async def chat(
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream agent response via Server-Sent Events.

    Flow:
    1. Ensure a DB ``ChatSession`` exists (created up front so its ID can be
       used as the ADK session ID — single ID, no mapping needed).
    2. Load existing messages from DB (used for ADK session reconstruction
       after a server restart).
    3. Run the agent, streaming events to the client.
    4. Persist the new user + assistant messages to DB.
    """

    # ── 1. Ensure DB session exists ──────────────────────────────────
    db_session = await _ensure_chat_session(db, user, body.session_id, body.message)
    await db.commit()  # flush + commit so the ID is stable

    # ── 2. Load history for session reconstruction ───────────────────
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == db_session.id)
        .order_by(ChatMessage.created_at)
    )
    db_messages = list(result.scalars().all())

    # Load persisted working-memory state for cold-start recovery (P1 fix)
    saved_state: dict[str, str] | None = None
    if db_session.state_json:
        try:
            saved_state = json.loads(db_session.state_json)
        except (json.JSONDecodeError, TypeError):
            saved_state = None

    # ── 3. Persist the user message *before* streaming starts ────────
    # This guarantees it is saved even if the SSE connection drops mid-stream.
    db.add(ChatMessage(session_id=db_session.id, role="user", content=body.message))
    await db.commit()

    async def event_generator():
        full_response: list[str] = []
        latest_state_snapshot: str | None = None
        artifact_ids: list[str] = []

        try:
            async for event_type, payload in run_agent_stream(
                user, body.message, db_session.id, db_messages, saved_state
            ):
                if event_type == "text":
                    full_response.append(payload)
                    yield f"data: {json.dumps({'type': 'text', 'content': payload})}\n\n"
                elif event_type == "text_reset":
                    full_response.clear()
                    yield f"data: {json.dumps({'type': 'text_reset'})}\n\n"
                elif event_type == "tool_call":
                    yield f"data: {json.dumps({'type': 'tool_call', 'content': payload})}\n\n"
                elif event_type == "tool_result":
                    yield f"data: {json.dumps({'type': 'tool_result', 'content': payload})}\n\n"
                elif event_type == "artifact":
                    # DBArtifactService already persisted the artifact to PostgreSQL.
                    # Track its ID so we can link it to the assistant message later.
                    artifact_info = json.loads(payload)
                    artifact_ids.append(artifact_info["artifact_id"])
                    yield f"data: {json.dumps({'type': 'artifact', **artifact_info})}\n\n"
                elif event_type == "state_snapshot":
                    # Capture but don't send to frontend — this is for DB persistence
                    latest_state_snapshot = payload
        except Exception:
            logger.exception("Error in SSE event generator for session %s", db_session.id)
            error_text = "\n\n⚠️ An error occurred. Please try again."
            full_response.append(error_text)
            yield f"data: {json.dumps({'type': 'text', 'content': error_text})}\n\n"

        # ── 4. Persist assistant response & working-memory state ───────
        assistant_text = "".join(full_response)

        if assistant_text:
            msg = ChatMessage(session_id=db_session.id, role="assistant", content=assistant_text)
            db.add(msg)
            await db.flush()  # populate msg.id

            # Link artifacts to this assistant message so they survive
            # session switches (loaded back via get_messages).
            if artifact_ids:
                await db.execute(
                    update(Artifact)
                    .where(Artifact.id.in_(artifact_ids))
                    .values(message_id=msg.id)
                )


        # Persist the working-memory snapshot so it survives server restarts
        if latest_state_snapshot is not None:
            db_session.state_json = latest_state_snapshot
        # Touch updated_at so the session list sorts by last activity
        db_session.updated_at = datetime.now(timezone.utc)
        await db.commit()

        # Final event — carries the session id
        done_payload = {
            "type": "done",
            "session_id": db_session.id,
        }
        yield f"data: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",          # nginx
            "Content-Encoding": "none",          # prevent gzip buffering
        },
    )


# ── Sessions CRUD ─────────────────────────────────────────────────────────

@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_user_session(db, user, session_id)

    # Load messages
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()

    # Load artifact metadata for this session (without the data blob)
    from sqlalchemy import func as sa_func

    art_result = await db.execute(
        select(
            Artifact.id,
            Artifact.message_id,
            Artifact.filename,
            Artifact.content_type,
            Artifact.created_at.label("art_created_at"),
            sa_func.octet_length(Artifact.data).label("size"),
        )
        .where(Artifact.session_id == session.id)
    )
    art_rows = art_result.all()

    # Group artifacts by message_id
    artifacts_by_msg: dict[str, list[dict]] = {}
    orphan_artifacts: list[tuple[datetime, dict]] = []  # (created_at, info)
    for row in art_rows:
        info = {
            "artifact_id": row.id,
            "filename": row.filename,
            "content_type": row.content_type,
            "size": row.size or 0,
        }
        if row.message_id:
            artifacts_by_msg.setdefault(row.message_id, []).append(info)
        else:
            # Orphan artifact (created before the message_id migration).
            # We'll attach it to the nearest assistant message below.
            orphan_artifacts.append((row.art_created_at, info))

    # Build response with artifacts attached to their messages
    response = []
    for msg in messages:
        item: dict = {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        arts = artifacts_by_msg.get(msg.id)
        if arts:
            item["artifacts"] = arts
        response.append(item)

    # Attach orphan artifacts to the nearest following assistant message
    # (artifact is created during tool execution → assistant message is
    # saved shortly after).  Fallback: last assistant message.
    if orphan_artifacts:
        assistant_items = [r for r in response if r["role"] == "assistant"]
        for art_ts, art_info in orphan_artifacts:
            attached = False
            for a_item in assistant_items:
                msg_ts = datetime.fromisoformat(a_item["created_at"])
                if art_ts and msg_ts >= art_ts:
                    a_item.setdefault("artifacts", []).append(art_info)
                    attached = True
                    break
            if not attached and assistant_items:
                # Fallback: attach to the last assistant message
                assistant_items[-1].setdefault("artifacts", []).append(art_info)

    return response


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_user_session(db, user, session_id)
    # Clean up the ADK in-memory session as well
    await delete_adk_session(user_id=user.id, session_id=session.id)
    await db.delete(session)
    await db.commit()


# ── Artifact download ─────────────────────────────────────────────────────

@router.get("/artifacts/{artifact_id}")
async def download_artifact(
    artifact_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a generated artifact (e.g. PDF quotation) by its ID."""
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id, Artifact.user_id == user.id)
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    from starlette.responses import Response

    return Response(
        content=artifact.data,
        media_type=artifact.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{artifact.filename}"',
            "Content-Length": str(len(artifact.data)),
        },
    )


# ── Helpers ───────────────────────────────────────────────────────────────

async def _get_user_session(db: AsyncSession, user: User, session_id: str) -> ChatSession:
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


async def _ensure_chat_session(
    db: AsyncSession, user: User, session_id: str | None, first_message: str,
) -> ChatSession:
    """Return an existing ChatSession or create a new one."""
    if session_id:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    # Auto-title from first message (truncated)
    title = first_message[:60] + ("…" if len(first_message) > 60 else "")
    new_session = ChatSession(user_id=user.id, title=title)
    db.add(new_session)
    await db.flush()  # populate .id
    return new_session
