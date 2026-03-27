from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ShipmentStatus(str, Enum):
    CREATED = "created"
    BOOKED = "booked"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELAYED = "delayed"
    CUSTOMS_HOLD = "customs_hold"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ShipmentMode(str, Enum):
    AIR = "air"
    SEA = "sea"
    TRUCK = "truck"
    RAIL = "rail"
    EXPRESS = "express"


class ShipmentEvent(BaseModel):
    timestamp: datetime
    location: str
    code: str
    description: str


class Shipment(BaseModel):
    shipment_id: str
    order_id: Optional[str] = None
    origin: str
    destination: str
    mode: ShipmentMode
    status: ShipmentStatus
    eta: datetime
    events: list[ShipmentEvent] = Field(default_factory=list)
    customer_reference: Optional[str] = None


class CreateShipmentRequest(BaseModel):
    origin: str = Field(..., min_length=2)
    destination: str = Field(..., min_length=2)
    mode: ShipmentMode = ShipmentMode.AIR
    weight_kg: float = Field(..., gt=0)
    goods_description: str = Field(..., min_length=2)
    order_id: Optional[str] = None
    customer_reference: Optional[str] = None

    @field_validator("origin", "destination", mode="before")
    @classmethod
    def strip_values(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class RateQuoteRequest(BaseModel):
    origin: str
    destination: str
    mode: ShipmentMode = ShipmentMode.AIR
    weight_kg: float = Field(..., gt=0)


class RateQuote(BaseModel):
    currency: str = "USD"
    amount: float
    estimated_transit_days: int
    surcharge_notes: list[str] = Field(default_factory=list)


class ApiError(BaseModel):
    code: str
    message: str
    retriable: bool = False


UTC = timezone.utc


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def eta_from_mode(mode: ShipmentMode) -> datetime:
    days_by_mode = {
        ShipmentMode.EXPRESS: 3,
        ShipmentMode.AIR: 5,
        ShipmentMode.TRUCK: 7,
        ShipmentMode.RAIL: 12,
        ShipmentMode.SEA: 28,
    }
    return now_utc() + timedelta(days=days_by_mode[mode])
