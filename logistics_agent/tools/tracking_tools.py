"""Shipment visibility tools: track and fees."""

from __future__ import annotations

from typing import Any

from google.adk.tools import ToolContext

from logistics_agent.services.logistics_service import LogisticsService
from logistics_agent.tools._common import resolve_service


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
                    return {
                        "status": "error",
                        "code": -1,
                        "msg": f"Invalid tracking number: {number}",
                        "detail": item["errormsg"],
                    }
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
        return resolve_service(tool_context).get_order_fees({"waybillnumber": [waybillnumber]})
    except Exception as exc:
        return LogisticsService.format_error(exc)

