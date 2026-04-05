"""Chat routes: SSE streaming, sessions CRUD, message history."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.auth.dependencies import get_current_user
from app.chat.adk_runner import delete_adk_session, run_agent_stream
from app.database import get_db
from app.models import ChatMessage, ChatSession, User
from app.schemas import (
    ChatMessageResponse,
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

    async def event_generator():
        full_response: list[str] = []

        async for event_type, payload in run_agent_stream(
            user, body.message, db_session.id, db_messages
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

        # ── 4. Persist new messages to DB ─────────────────────────────
        assistant_text = "".join(full_response)

        db.add(ChatMessage(session_id=db_session.id, role="user", content=body.message))
        if assistant_text:
            db.add(ChatMessage(session_id=db_session.id, role="assistant", content=assistant_text))
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


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_user_session(db, user, session_id)
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
    )
    return result.scalars().all()


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
