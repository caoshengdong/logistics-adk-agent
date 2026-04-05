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

import json as _json
import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from google.adk.agents.run_config import RunConfig, StreamingMode
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

def _refresh_session_credentials(user: User, session_id: str) -> None:
    """Update auth state in InMemorySessionService's *internal* storage.

    ``get_session()`` returns a **deep copy** of the stored session, so
    mutating the returned object's ``.state`` is silently discarded.  We
    must reach into the internal ``sessions`` dict to persist changes that
    the runner (which re-fetches the session) will actually see.
    """
    internal = (
        session_service.sessions
        .get(backend_settings.adk_app_name, {})
        .get(user.id, {})
        .get(session_id)
    )
    if internal is None:
        return
    internal.state["auth_code"] = user.customer_code
    internal.state["auth_token"] = user.auth_token
    internal.state["customer_code"] = user.customer_code
    internal.state["customer_name"] = user.display_name


async def get_or_create_session(
    user: User,
    session_id: str,
    db_messages: list[ChatMessage] | None = None,
    saved_state: dict[str, str] | None = None,
):
    """Return an existing ADK session or create one (possibly with history).

    ``session_id`` is the DB ``ChatSession.id`` — we use it verbatim as the
    ADK session ID so both layers share a single identifier.

    If the ADK in-memory session is missing (e.g. after a server restart) but
    ``db_messages`` are supplied, the session is *reconstructed*: a fresh ADK
    session is created, and historical messages are replayed as Events so the
    LLM retains prior conversation context.

    ``saved_state`` is the persisted working-memory snapshot (``last_*`` keys)
    from the DB.  When provided it is merged into the initial state so that
    tool-produced context survives server restarts.
    """

    # 1. Try to find an existing in-memory session
    existing = await session_service.get_session(
        app_name=backend_settings.adk_app_name,
        user_id=user.id,
        session_id=session_id,
    )
    if existing:
        # Refresh credentials — the user may have updated their profile
        # (customer_code / auth_token) since this ADK session was created.
        # NOTE: existing is a deep copy; we must update the *internal* storage.
        _refresh_session_credentials(user, session_id)
        return existing

    # 2. Create a fresh ADK session with this exact ID.
    #    Every key referenced via {key} in any agent instruction MUST exist
    #    in the initial state — ADK's template engine raises KeyError otherwise.
    initial_state = {
        # ── Auth / identity (ephemeral — never persisted to DB) ──
        "auth_code": user.customer_code,
        "auth_token": user.auth_token,
        "customer_code": user.customer_code,
        "customer_name": user.display_name,
        # ── Working-memory keys (populated by tools as they run) ──
        "last_waybill": "",
        "last_order_channel": "",
        "last_order_destination": "",
        "last_order_status": "",
        "last_order_recipient": "",
        "last_orders_summary": "",
        "last_quote_summary": "",
        "last_cheapest_channel": "",
        "last_estimate_channel": "",
        "last_estimate_total": "",
        "last_tracked_waybill": "",
        "last_tracked_status": "",
        "last_fees_waybill": "",
        "last_fees_total": "",
    }

    # Overlay persisted working-memory snapshot so cold-start recovery
    # restores tool-produced context (last_waybill, last_tracked_status, …).
    # NEVER restore ephemeral auth keys from the DB — they come from the User row.
    if saved_state:
        for key, value in saved_state.items():
            if key in initial_state and key not in _EPHEMERAL_KEYS:
                initial_state[key] = value

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
    for invocation_counter, msg in enumerate(db_messages, start=1):
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

# Keys that are injected fresh from the User row on every session create /
# refresh and must NEVER be persisted in the DB state snapshot.
_EPHEMERAL_KEYS = frozenset({
    "auth_code", "auth_token", "customer_code", "customer_name",
})


async def run_agent_stream(
    user: User,
    message: str,
    session_id: str,
    db_messages: list[ChatMessage] | None = None,
    saved_state: dict[str, str] | None = None,
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
    saved_state : dict[str, str] | None
        Persisted working-memory snapshot (``last_*`` keys) from the DB.
        Used to restore state on cold start.

    Yields
    ------
    tuple[str, str]
        ``("text", chunk)``              — agent text output (streamed token-by-token)
        ``("text_reset", "")``           — new speaker; clear accumulated text
        ``("tool_call", json_string)``   — agent invoked a tool
        ``("tool_result", json_string)`` — tool returned a result
        ``("state_snapshot", json)``     — working-memory snapshot for persistence
        ``("session_id", id)``           — final event with session id
    """
    session = await get_or_create_session(user, session_id, db_messages, saved_state)

    content = types.Content(role="user", parts=[types.Part(text=message)])

    # Enable true LLM-level streaming so the model yields tokens as they are
    # generated instead of waiting for the full response.
    run_config = RunConfig(streaming_mode=StreamingMode.SSE)

    # Track which agent last produced text.  When the speaking agent changes,
    # we send a "text_reset" event so the frontend clears previously streamed
    # text.  This prevents duplicates (sub-agent text + root-agent summary)
    # while still working when the root agent produces no text of its own.
    last_text_author: str | None = None

    # In SSE streaming mode, partial events carry incremental text deltas
    # while the final (non-partial) event carries the *full* accumulated text.
    # If we already streamed partial deltas, we must skip the final event's
    # text to avoid sending the content twice.
    has_streamed_partial = False

    async for event in runner.run_async(
        user_id=user.id,
        session_id=session.id,
        new_message=content,
        run_config=run_config,
    ):
        event_author = getattr(event, "author", None) or ""
        is_partial = getattr(event, "partial", None) is True

        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    if is_partial:
                        # Partial event — stream the incremental delta
                        if last_text_author is not None and event_author != last_text_author:
                            yield ("text_reset", "")
                            has_streamed_partial = False
                        last_text_author = event_author
                        has_streamed_partial = True
                        yield ("text", part.text)
                    else:
                        # Final (non-partial) event — only yield if no
                        # partials were streamed (otherwise it's a duplicate
                        # of the already-streamed content).
                        if not has_streamed_partial:
                            if last_text_author is not None and event_author != last_text_author:
                                yield ("text_reset", "")
                            last_text_author = event_author
                            yield ("text", part.text)
                        # Reset for the next streaming segment
                        has_streamed_partial = False

                # Tool calls / results only appear in non-partial events;
                # partial function_call parts are incomplete and must be
                # skipped (ADK does not execute them either).
                if not is_partial and part.function_call:
                    fc = part.function_call
                    yield ("tool_call", _json.dumps({
                        "name": fc.name,
                        "args": dict(fc.args) if fc.args else {},
                    }))

                if not is_partial and part.function_response:
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

    # ── Snapshot working-memory state for DB persistence ──
    # Re-fetch the session to get the latest state (after tool mutations).
    final_session = await session_service.get_session(
        app_name=backend_settings.adk_app_name,
        user_id=user.id,
        session_id=session.id,
    )
    if final_session:
        working_memory = {
            k: v for k, v in final_session.state.items()
            if k.startswith("last_") and k not in _EPHEMERAL_KEYS
        }
        yield ("state_snapshot", _json.dumps(working_memory, ensure_ascii=False))

    # Always tell the caller which session this belongs to
    yield ("session_id", session.id)



