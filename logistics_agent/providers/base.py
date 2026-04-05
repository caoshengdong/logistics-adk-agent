from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from logistics_agent.models.domain import (
    ChannelPriceRequest,
    CreateOrderRequest,
    DeleteOrderRequest,
    DestQueryParams,
    OrderFeesRequest,
    PriceQueryRequest,
    QueryOrdersRequest,
    TrackRequest,
)


class LogisticsProvider(ABC):
    """Abstract provider interface aligned with the logistics system API."""

    @abstractmethod
    def create_order(self, request: CreateOrderRequest) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def query_orders(self, request: QueryOrdersRequest) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def track_shipment(self, request: TrackRequest) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def estimate_channel_price(self, request: ChannelPriceRequest) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def query_price(self, request: PriceQueryRequest) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def query_channels(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def query_destinations(self, params: DestQueryParams) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_order_fees(self, request: OrderFeesRequest) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def delete_order(self, request: DeleteOrderRequest) -> dict[str, Any]:
        raise NotImplementedError
