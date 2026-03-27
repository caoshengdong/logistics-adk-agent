from __future__ import annotations

from abc import ABC, abstractmethod

from logistics_agent.models.domain import CreateShipmentRequest, RateQuote, RateQuoteRequest, Shipment


class LogisticsProvider(ABC):
    @abstractmethod
    def get_shipment_by_order_id(self, order_id: str) -> Shipment:
        raise NotImplementedError

    @abstractmethod
    def get_shipment_by_shipment_id(self, shipment_id: str) -> Shipment:
        raise NotImplementedError

    @abstractmethod
    def create_shipment(self, request: CreateShipmentRequest) -> Shipment:
        raise NotImplementedError

    @abstractmethod
    def quote_rate(self, request: RateQuoteRequest) -> RateQuote:
        raise NotImplementedError
