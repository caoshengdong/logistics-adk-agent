from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from logistics_agent.models.domain import CreateShipmentRequest, RateQuoteRequest
from logistics_agent.providers.base import LogisticsProvider
from logistics_agent.providers.mock_provider import ShipmentNotFoundError
from logistics_agent.utils.presenters import latest_event_summary


@dataclass
class LogisticsService:
    provider: LogisticsProvider

    def track_order(self, order_id: str) -> dict[str, Any]:
        shipment = self.provider.get_shipment_by_order_id(order_id)
        shipment_payload = shipment.model_dump(mode="json")
        return {
            "status": "success",
            "lookup_type": "order_id",
            "order_id": order_id,
            "summary": {
                "shipment_id": shipment.shipment_id,
                "current_status": shipment.status.value,
                "eta": shipment.eta.isoformat(),
                "latest_event": latest_event_summary(shipment_payload),
            },
            "shipment": shipment_payload,
        }

    def track_shipment(self, shipment_id: str) -> dict[str, Any]:
        shipment = self.provider.get_shipment_by_shipment_id(shipment_id)
        shipment_payload = shipment.model_dump(mode="json")
        return {
            "status": "success",
            "lookup_type": "shipment_id",
            "shipment_id": shipment_id,
            "summary": {
                "order_id": shipment.order_id,
                "current_status": shipment.status.value,
                "eta": shipment.eta.isoformat(),
                "latest_event": latest_event_summary(shipment_payload),
            },
            "shipment": shipment_payload,
        }

    def create_shipment(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = CreateShipmentRequest.model_validate(payload)
        shipment = self.provider.create_shipment(request)
        return {
            "status": "success",
            "message": "Shipment created successfully.",
            "shipment": shipment.model_dump(mode="json"),
        }

    def quote_rate(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = RateQuoteRequest.model_validate(payload)
        quote = self.provider.quote_rate(request)
        return {
            "status": "success",
            "quote": quote.model_dump(mode="json"),
        }

    @staticmethod
    def format_error(exc: Exception) -> dict[str, Any]:
        if isinstance(exc, ShipmentNotFoundError):
            return {
                "status": "error",
                "error": {
                    "code": "SHIPMENT_NOT_FOUND",
                    "message": str(exc),
                    "retriable": False,
                },
            }
        if hasattr(exc, "errors"):
            return {
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Input validation failed.",
                    "details": exc.errors(),
                    "retriable": False,
                },
            }
        return {
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
                "retriable": False,
            },
        }
