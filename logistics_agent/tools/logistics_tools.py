from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional

from logistics_agent.providers.factory import get_provider
from logistics_agent.services.logistics_service import LogisticsService


@lru_cache(maxsize=1)
def _service() -> LogisticsService:
    return LogisticsService(provider=get_provider())


def get_order_shipping_status(order_id: str) -> dict[str, Any]:
    """Look up a shipment by order ID and return status, ETA, route, and latest tracking event.

    Args:
        order_id: Business order number such as "12345".
    """
    try:
        return _service().track_order(order_id=order_id)
    except Exception as exc:  # pragma: no cover - tool boundary
        return LogisticsService.format_error(exc)



def get_shipment_status(shipment_id: str) -> dict[str, Any]:
    """Look up a shipment by shipment ID and return status, ETA, route, and tracking events.

    Args:
        shipment_id: Internal shipment identifier such as "SHP-10001".
    """
    try:
        return _service().track_shipment(shipment_id=shipment_id)
    except Exception as exc:  # pragma: no cover - tool boundary
        return LogisticsService.format_error(exc)



def create_freight_shipment(
    origin: str,
    destination: str,
    weight_kg: float,
    goods_description: str,
    mode: str = "air",
    order_id: Optional[str] = None,
    customer_reference: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new freight shipment.

    Args:
        origin: Origin city/country string.
        destination: Destination city/country string.
        weight_kg: Cargo weight in kilograms.
        goods_description: Short cargo description for operations context.
        mode: One of air, sea, truck, rail, express.
        order_id: Optional business order reference.
        customer_reference: Optional customer PO or internal reference.
    """
    try:
        return _service().create_shipment(
            {
                "origin": origin,
                "destination": destination,
                "weight_kg": weight_kg,
                "goods_description": goods_description,
                "mode": mode,
                "order_id": order_id,
                "customer_reference": customer_reference,
            }
        )
    except Exception as exc:  # pragma: no cover - tool boundary
        return LogisticsService.format_error(exc)



def quote_freight_rate(
    origin: str,
    destination: str,
    weight_kg: float,
    mode: str = "air",
) -> dict[str, Any]:
    """Estimate a freight quote using origin, destination, weight in kg, and transport mode."""
    try:
        return _service().quote_rate(
            {
                "origin": origin,
                "destination": destination,
                "weight_kg": weight_kg,
                "mode": mode,
            }
        )
    except Exception as exc:  # pragma: no cover - tool boundary
        return LogisticsService.format_error(exc)
