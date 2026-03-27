from __future__ import annotations

"""HTTP provider scaffold for replacing the mock integration.

This module is intentionally not wired in by default because the assessment
environment does not provide working API credentials and the supplied API docs
were unreachable from this execution environment.

The goal is to make the integration seam explicit and interview-friendly:
- the agent and tools remain stable
- transport/auth concerns live here
- response normalization stays isolated from the LLM layer
"""

from dataclasses import dataclass
from typing import Any

from logistics_agent.models.domain import (
    CreateShipmentRequest,
    RateQuote,
    RateQuoteRequest,
    Shipment,
    ShipmentEvent,
    ShipmentMode,
    ShipmentStatus,
)
from logistics_agent.providers.base import LogisticsProvider


class ProviderConfigurationError(RuntimeError):
    pass


@dataclass
class HttpLogisticsProvider(LogisticsProvider):
    base_url: str
    api_key: str
    timeout_seconds: float = 10.0

    def get_shipment_by_order_id(self, order_id: str) -> Shipment:
        payload = self._request("GET", f"/orders/{order_id}/shipment")
        return self._to_shipment(payload)

    def get_shipment_by_shipment_id(self, shipment_id: str) -> Shipment:
        payload = self._request("GET", f"/shipments/{shipment_id}")
        return self._to_shipment(payload)

    def create_shipment(self, request: CreateShipmentRequest) -> Shipment:
        payload = self._request("POST", "/shipments", json=request.model_dump(mode="json"))
        return self._to_shipment(payload)

    def quote_rate(self, request: RateQuoteRequest) -> RateQuote:
        payload = self._request("POST", "/quotes", json=request.model_dump(mode="json"))
        return RateQuote.model_validate(payload)

    def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Replace with real HTTP transport.

        Suggested implementation details for a real submission extension:
        - use httpx.Client with timeout + retries
        - attach auth headers
        - map non-2xx responses into provider-specific exceptions
        - log request ids for observability
        - keep raw payload shape confined to this adapter
        """
        raise NotImplementedError(
            "HttpLogisticsProvider is a scaffold only. Wire this to the real API once "
            "the endpoint schema and credentials are available."
        )

    @staticmethod
    def _to_shipment(payload: dict[str, Any]) -> Shipment:
        """Normalize external payloads into internal domain models.

        The exact field mapping will depend on the real API schema. This method
        is deliberately explicit so the integration work remains localized.
        """
        events = [
            ShipmentEvent(
                timestamp=event["timestamp"],
                location=event["location"],
                code=event["code"],
                description=event["description"],
            )
            for event in payload.get("events", [])
        ]
        return Shipment(
            shipment_id=payload["shipment_id"],
            order_id=payload.get("order_id"),
            origin=payload["origin"],
            destination=payload["destination"],
            mode=ShipmentMode(payload["mode"]),
            status=ShipmentStatus(payload["status"]),
            eta=payload["eta"],
            customer_reference=payload.get("customer_reference"),
            events=events,
        )
