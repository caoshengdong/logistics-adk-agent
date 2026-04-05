"""Shipment visibility tools: track and fees."""

from __future__ import annotations

from typing import Any

from google.adk.tools import ToolContext

from agent.services.logistics_service import LogisticsService
from agent.tools._common import resolve_service


def _save_state(tool_context: ToolContext | None, key: str, value: Any) -> None:
    """Write a value into ADK session state (for cross-agent context sharing)."""
    if tool_context is not None:
        tool_context.state[key] = value


def track_shipment(
    number: str, number_type: str = "waybillnumber",
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Track a shipment by its number. Returns tracking events and order status.

    Args:
        number: The tracking number to look up.
        number_type: Type of number: "waybillnumber", "systemnumber", or "customernumber".
    """
    try:
        result = resolve_service(tool_context).track_shipment({number_type: [number]})
        # Check if the number was invalid — surface the error clearly so the
        # agent does NOT retry with a different number_type.
        if result.get("data"):
            for item in result["data"]:
                if item.get("errormsg"):
                    # ── Clear stale tracking state so follow-ups don't
                    #    reference the previous (now irrelevant) shipment. ──
                    _save_state(tool_context, "last_tracked_waybill", "")
                    _save_state(tool_context, "last_tracked_status", "")
                    return {
                        "status": "error",
                        "code": -1,
                        "msg": f"Invalid tracking number: {number}",
                        "detail": item["errormsg"],
                    }
            # ── Compress into state for follow-up turns ──
            first = result["data"][0]
            _save_state(tool_context, "last_tracked_waybill",
                        first.get("waybillnumber", number))
            _save_state(tool_context, "last_tracked_status",
                        first.get("orderstatusName", first.get("orderstatus", "")))
        return result
    except Exception as exc:
        return LogisticsService.format_error(exc)


def get_order_fees(
    waybillnumber: str,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Get the fee breakdown for an order by its waybill number.

    Args:
        waybillnumber: The waybill number to query fees for.
    """
    try:
        result = resolve_service(tool_context).get_order_fees({"waybillnumber": [waybillnumber]})
        # ── Compress into state: total fee amount ──
        if result.get("status") == "success" and result.get("data"):
            first = result["data"][0]
            fees_list = first.get("recsheetList", [])
            total = sum(f.get("amount", 0) for f in fees_list)
            _save_state(tool_context, "last_fees_waybill", waybillnumber)
            _save_state(tool_context, "last_fees_total", f"{total:.2f} RMB")
        return result
    except Exception as exc:
        return LogisticsService.format_error(exc)

