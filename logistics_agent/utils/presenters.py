from __future__ import annotations

from typing import Any


def latest_event_summary(shipment: dict[str, Any]) -> str:
    events = shipment.get("events", [])
    if not events:
        return "No tracking events available."
    latest = events[-1]
    return f"{latest['code']} at {latest['location']}: {latest['description']}"
