from __future__ import annotations

from typing import Any


def latest_track_summary(track_result: dict[str, Any]) -> str:
    """Summarize the latest tracking event from a track result."""
    items = track_result.get("trackItems", [])
    if not items:
        return "暂无轨迹信息"
    latest = items[-1]
    return f"[{latest.get('trackdate_utc8', '')}] {latest.get('location', '')}: {latest.get('info', '')}"


def format_price_comparison(price_results: list[dict[str, Any]]) -> str:
    """Format multiple channel price quotes into a readable comparison."""
    if not price_results:
        return "暂无报价信息"
    lines = []
    for i, pr in enumerate(price_results, 1):
        ch = pr.get("channel", {})
        name = ch.get("channelnamecn") or ch.get("channelname") or ch.get("channelid", "")
        aging = ch.get("aging", "")
        total = pr.get("totalCost", 0)
        ccy = pr.get("totalCostCcy", "RMB")
        lines.append(f"{i}. {name} — {ccy} {total:.2f} (时效: {aging})")
    return "\n".join(lines)
