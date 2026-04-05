"""ADK Runner & Session management — bridges FastAPI ↔ Google ADK agents.

Key responsibility: inject per-user credentials (customer_code, auth_token)
into the ADK session state so that every tool call can pick them up via
``ToolContext.state``.
"""

from __future__ import annotations

import asyncio
import json as _json
import logging
from typing import AsyncGenerator

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from backend.app.config import backend_settings
from backend.app.models import User
from logistics_agent.agent import root_agent

logger = logging.getLogger(__name__)

# Shared ADK session service — keeps sessions in memory.
# For production persistence, swap with a database-backed implementation.
session_service = InMemorySessionService()

# Single shared Runner — the agent graph is stateless; state lives in Session.
runner = Runner(
    agent=root_agent,
    app_name=backend_settings.adk_app_name,
    session_service=session_service,
)


async def get_or_create_session(user: User, session_id: str | None = None):
    """Return an existing ADK session or create a fresh one with user context."""

    if session_id:
        existing = await session_service.get_session(
            app_name=backend_settings.adk_app_name,
            user_id=user.id,
            session_id=session_id,
        )
        if existing:
            return existing

    # Create new session with user credentials in state ← this is the magic!
    session = await session_service.create_session(
        app_name=backend_settings.adk_app_name,
        user_id=user.id,
        state={
            "auth_code": user.customer_code,
            "auth_token": user.auth_token,
            "customer_code": user.customer_code,
            "customer_name": user.display_name,
        },
    )
    logger.info("Created ADK session %s for user %s", session.id, user.id)
    return session


async def run_agent_stream(
    user: User,
    message: str,
    session_id: str | None = None,
) -> AsyncGenerator[tuple[str, str], None]:
    """Run the agent and yield (event_type, payload) tuples.

    Event types
    -----------
    - ``("text", chunk)``              — agent text output
    - ``("text_reset", "")``           — new speaker; frontend should clear accumulated text
    - ``("tool_call", json_string)``   — agent invoked a tool
    - ``("tool_result", json_string)`` — tool returned a result
    - ``("session_id", id)``           — final event with session id
    """
    session = await get_or_create_session(user, session_id)

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
                    # When a different agent starts speaking, tell the
                    # frontend to discard the previous text and start fresh.
                    if last_text_author is not None and event_author != last_text_author:
                        yield ("text_reset", "")
                    last_text_author = event_author

                    for chunk in _iter_word_chunks(part.text):
                        yield ("text", chunk)
                        await asyncio.sleep(0)

                # Tool call — forward from any agent
                if part.function_call:
                    fc = part.function_call
                    yield ("tool_call", _json.dumps({
                        "name": fc.name,
                        "args": dict(fc.args) if fc.args else {},
                    }))
                # Tool response — forward from any agent
                if part.function_response:
                    fr = part.function_response
                    resp_str = _json.dumps(fr.response if fr.response else {}, ensure_ascii=False, default=str)
                    if len(resp_str) > 800:
                        resp_str = resp_str[:800] + "…"
                    yield ("tool_result", _json.dumps({
                        "name": fr.name,
                        "response": resp_str,
                    }))

    # Always tell the caller which session this belongs to
    yield ("session_id", session.id)


def _iter_word_chunks(text: str, max_chars: int = 6):
    """Break *text* into small chunks for progressive streaming.

    Splits on whitespace boundaries, yielding at most *max_chars* characters
    per chunk (preserving the leading space).  Chinese / CJK text (no spaces)
    is split character-by-character so it still streams smoothly.
    """
    import re

    # Split into tokens: each token is either a whitespace segment or a word
    tokens = re.findall(r"\S+|\s+", text)
    buf = ""
    for tok in tokens:
        buf += tok
        if len(buf) >= max_chars:
            yield buf
            buf = ""
    if buf:
        yield buf


