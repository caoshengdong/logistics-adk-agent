"""Shipment visibility tools: track and fees."""

from __future__ import annotations

from typing import Any

from logistics_agent.services.logistics_service import LogisticsService
from logistics_agent.tools._common import get_service


def track_shipment(number: str, number_type: str = "waybillnumber") -> dict[str, Any]:
    """Track a shipment by its number. Returns tracking events and order status.

    Args:
        number: The tracking number to look up.
        number_type: Type of number: "waybillnumber", "systemnumber", or "customernumber".
    """
    try:
        return get_service().track_shipment({number_type: [number]})
    except Exception as exc:
        return LogisticsService.format_error(exc)


def get_order_fees(waybillnumber: str) -> dict[str, Any]:
    """Get the fee breakdown for an order by its waybill number.

    Args:
        waybillnumber: The waybill number to query fees for.
    """
    try:
        return get_service().get_order_fees({"waybillnumber": [waybillnumber]})
    except Exception as exc:
        return LogisticsService.format_error(exc)

