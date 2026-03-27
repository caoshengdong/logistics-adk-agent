from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict
from uuid import uuid4

from logistics_agent.models.domain import (
    CreateShipmentRequest,
    RateQuote,
    RateQuoteRequest,
    Shipment,
    ShipmentEvent,
    ShipmentMode,
    ShipmentStatus,
    eta_from_mode,
    now_utc,
)
from logistics_agent.providers.base import LogisticsProvider


class ShipmentNotFoundError(ValueError):
    pass


@dataclass
class MockLogisticsProvider(LogisticsProvider):
    shipments_by_id: Dict[str, Shipment] = field(default_factory=dict)
    order_to_shipment: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.shipments_by_id:
            return
        self._seed_data()

    def _seed_data(self) -> None:
        shipment = Shipment(
            shipment_id="SHP-10001",
            order_id="12345",
            origin="Shenzhen, CN",
            destination="Los Angeles, US",
            mode=ShipmentMode.AIR,
            status=ShipmentStatus.IN_TRANSIT,
            eta=now_utc() + timedelta(days=2),
            customer_reference="PO-7788",
            events=[
                ShipmentEvent(
                    timestamp=now_utc() - timedelta(days=3),
                    location="Shenzhen, CN",
                    code="BOOKED",
                    description="Shipment booked with carrier.",
                ),
                ShipmentEvent(
                    timestamp=now_utc() - timedelta(days=2, hours=5),
                    location="Shenzhen, CN",
                    code="PICKED_UP",
                    description="Cargo picked up from origin warehouse.",
                ),
                ShipmentEvent(
                    timestamp=now_utc() - timedelta(days=1, hours=7),
                    location="Hong Kong, CN",
                    code="DEPARTED",
                    description="Flight departed origin hub.",
                ),
            ],
        )
        self.shipments_by_id[shipment.shipment_id] = shipment
        self.order_to_shipment[shipment.order_id or ""] = shipment.shipment_id

    def get_shipment_by_order_id(self, order_id: str) -> Shipment:
        shipment_id = self.order_to_shipment.get(order_id)
        if not shipment_id:
            raise ShipmentNotFoundError(f"No shipment found for order_id={order_id}")
        return self.shipments_by_id[shipment_id]

    def get_shipment_by_shipment_id(self, shipment_id: str) -> Shipment:
        shipment = self.shipments_by_id.get(shipment_id)
        if not shipment:
            raise ShipmentNotFoundError(f"No shipment found for shipment_id={shipment_id}")
        return shipment

    def create_shipment(self, request: CreateShipmentRequest) -> Shipment:
        shipment_id = f"SHP-{str(uuid4())[:8].upper()}"
        shipment = Shipment(
            shipment_id=shipment_id,
            order_id=request.order_id,
            origin=request.origin,
            destination=request.destination,
            mode=request.mode,
            status=ShipmentStatus.CREATED,
            eta=eta_from_mode(request.mode),
            customer_reference=request.customer_reference,
            events=[
                ShipmentEvent(
                    timestamp=now_utc(),
                    location=request.origin,
                    code="CREATED",
                    description=f"Shipment created for {request.goods_description}.",
                )
            ],
        )
        self.shipments_by_id[shipment_id] = shipment
        if request.order_id:
            self.order_to_shipment[request.order_id] = shipment_id
        return shipment

    def quote_rate(self, request: RateQuoteRequest) -> RateQuote:
        mode_base = {
            ShipmentMode.EXPRESS: 11.5,
            ShipmentMode.AIR: 8.0,
            ShipmentMode.TRUCK: 3.5,
            ShipmentMode.RAIL: 2.8,
            ShipmentMode.SEA: 1.2,
        }
        route_factor = 1.6 if request.origin != request.destination else 1.0
        amount = round(mode_base[request.mode] * request.weight_kg * route_factor, 2)
        transit_days = {
            ShipmentMode.EXPRESS: 3,
            ShipmentMode.AIR: 5,
            ShipmentMode.TRUCK: 7,
            ShipmentMode.RAIL: 12,
            ShipmentMode.SEA: 28,
        }[request.mode]
        notes = ["Mock quote based on configured weight and transport mode."]
        if request.weight_kg > 100:
            notes.append("Heavy cargo surcharge likely applies in the real API.")
        return RateQuote(amount=amount, estimated_transit_days=transit_days, surcharge_notes=notes)
