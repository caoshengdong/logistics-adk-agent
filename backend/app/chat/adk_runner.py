"""ADK Runner & Session management — bridges FastAPI ↔ Google ADK agents.

Key responsibilities:
- Inject per-user credentials into ADK session state so every tool call can
  pick them up via ``ToolContext.state``.
- Use the DB ``ChatSession.id`` directly as the ADK session ID (single ID,
  no mapping needed).
- On cold start (server restart), reconstruct the ADK in-memory session from
  persisted ``ChatMessage`` records so conversation context is preserved.
"""

from __future__ import annotations

import asyncio
import json as _json
import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent.agent import root_agent
from app.config import backend_settings
from app.models import User

if TYPE_CHECKING:
    from app.models import ChatMessage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared ADK infrastructure
# ---------------------------------------------------------------------------

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=backend_settings.adk_app_name,
    session_service=session_service,
)

# Name of the root agent — used as author when reconstructing assistant events
_ROOT_AGENT_NAME = root_agent.name  # "logistics_agent"


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

async def get_or_create_session(
    user: User,
    session_id: str,
    db_messages: list[ChatMessage] | None = None,
):
    """Return an existing ADK session or create one (possibly with history).

    ``session_id`` is the DB ``ChatSession.id`` — we use it verbatim as the
    ADK session ID so both layers share a single identifier.

    If the ADK in-memory session is missing (e.g. after a server restart) but
    ``db_messages`` are supplied, the session is *reconstructed*: a fresh ADK
    session is created, and historical messages are replayed as Events so the
    LLM retains prior conversation context.
    """

    # 1. Try to find an existing in-memory session
    existing = await session_service.get_session(
        app_name=backend_settings.adk_app_name,
        user_id=user.id,
        session_id=session_id,
    )
    if existing:
        return existing

    # 2. Create a fresh ADK session with this exact ID
    initial_state = {
        "auth_code": user.customer_code,
        "auth_token": user.auth_token,
        "customer_code": user.customer_code,
        "customer_name": user.display_name,
    }

    session = await session_service.create_session(
        app_name=backend_settings.adk_app_name,
        user_id=user.id,
        session_id=session_id,
        state=initial_state,
    )

    # 3. Replay persisted history so the LLM sees prior turns
    if db_messages:
        await _replay_history(session, db_messages)
        logger.info(
            "Reconstructed ADK session %s for user %s with %d historical messages",
            session_id, user.id, len(db_messages),
        )
    else:
        logger.info("Created fresh ADK session %s for user %s", session_id, user.id)

    return session


async def delete_adk_session(user_id: str, session_id: str) -> None:
    """Remove an ADK session from memory (called when DB session is deleted)."""
    try:
        await session_service.delete_session(
            app_name=backend_settings.adk_app_name,
            user_id=user_id,
            session_id=session_id,
        )
        logger.info("Deleted ADK session %s", session_id)
    except Exception:
        # Session may not exist in memory (already evicted / server restarted)
        pass


# ---------------------------------------------------------------------------
# History reconstruction
# ---------------------------------------------------------------------------

async def _replay_history(session, db_messages: list[ChatMessage]) -> None:
    """Inject DB messages into an ADK session as Events.

    This allows the LLM to see the full conversation history even after a
    server restart wiped the ``InMemorySessionService``.
    """
    invocation_counter = 0

    for msg in db_messages:
        invocation_counter += 1
        invocation_id = f"history-{invocation_counter}"

        if msg.role == "user":
            event = Event(
                author="user",
                invocation_id=invocation_id,
                content=types.Content(
                    role="user",
                    parts=[types.Part(text=msg.content)],
                ),
                actions=EventActions(state_delta={}, artifact_delta={}),
                timestamp=msg.created_at.timestamp(),
            )
        else:
            # assistant message
            event = Event(
                author=_ROOT_AGENT_NAME,
                invocation_id=invocation_id,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=msg.content)],
                ),
                actions=EventActions(state_delta={}, artifact_delta={}),
                turn_complete=True,
                timestamp=msg.created_at.timestamp(),
            )

        await session_service.append_event(session=session, event=event)


# ---------------------------------------------------------------------------
# Agent execution (streaming)
# ---------------------------------------------------------------------------

async def run_agent_stream(
    user: User,
    message: str,
    session_id: str,
    db_messages: list[ChatMessage] | None = None,
) -> AsyncGenerator[tuple[str, str], None]:
    """Run the agent and yield ``(event_type, payload)`` tuples.

    Parameters
    ----------
    user : User
        The authenticated user.
    message : str
        The new user message.
    session_id : str
        The DB ``ChatSession.id`` — used as the ADK session ID.
    db_messages : list[ChatMessage] | None
        Existing messages for this session (from DB). Used to reconstruct
        the ADK session if it was lost from memory.

    Yields
    ------
    tuple[str, str]
        ``("text", chunk)``              — agent text output
        ``("text_reset", "")``           — new speaker; clear accumulated text
        ``("tool_call", json_string)``   — agent invoked a tool
        ``("tool_result", json_string)`` — tool returned a result
        ``("session_id", id)``           — final event with session id
    """
    session = await get_or_create_session(user, session_id, db_messages)

    content = types.Content(role="user", parts=[types.Part(text=message)])

    # Track which agent last produced text.  When the speaking agent changes,
    # we send a "text_reset" event so the frontend clears previously streamed
    # text.  This prevents duplicates (sub-agent text + root-agent summary)
    # while still working when the root agent produces no text of its own.
    last_text_author: str | None = None

    async for event in runner.run_async(
        user_id=user.id,
        session_id=session.id,
        new_message=content,
    ):
        event_author = getattr(event, "author", None) or ""

        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    if last_text_author is not None and event_author != last_text_author:
                        yield ("text_reset", "")
                    last_text_author = event_author

                    for chunk in _iter_word_chunks(part.text):
                        yield ("text", chunk)
                        await asyncio.sleep(0)

                if part.function_call:
                    fc = part.function_call
                    yield ("tool_call", _json.dumps({
                        "name": fc.name,
                        "args": dict(fc.args) if fc.args else {},
                    }))

                if part.function_response:
                    fr = part.function_response
                    resp_str = _json.dumps(
                        fr.response if fr.response else {},
                        ensure_ascii=False, default=str,
                    )
                    if len(resp_str) > 800:
                        resp_str = resp_str[:800] + "…"
                    yield ("tool_result", _json.dumps({
                        "name": fr.name,
                        "response": resp_str,
                    }))

    # Always tell the caller which session this belongs to
    yield ("session_id", session.id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_word_chunks(text: str, max_chars: int = 6):
    """Break *text* into small chunks for progressive streaming."""
    import re

    tokens = re.findall(r"\S+|\s+", text)
    buf = ""
    for tok in tokens:
        buf += tok
        if len(buf) >= max_chars:
            yield buf
            buf = ""
    if buf:
        yield buf

