from __future__ import annotations

from dataclasses import dataclass
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
from logistics_agent.providers.base import LogisticsProvider
from logistics_agent.providers.mock_provider import OrderNotFoundError


@dataclass
class LogisticsService:
    provider: LogisticsProvider

    # ----- 下单 -----
    def create_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = CreateOrderRequest.model_validate(payload)
        result = self.provider.create_order(request)
        return {"status": "success", **result}

    # ----- 查询运单 -----
    def query_orders(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = QueryOrdersRequest.model_validate(payload)
        result = self.provider.query_orders(request)
        return {"status": "success", **result}

    # ----- 轨迹追踪 -----
    def track_shipment(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = TrackRequest.model_validate(payload)
        result = self.provider.track_shipment(request)
        return {"status": "success", **result}

    # ----- 运费试算（指定渠道） -----
    def estimate_channel_price(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = ChannelPriceRequest.model_validate(payload)
        result = self.provider.estimate_channel_price(request)
        return {"status": "success", **result}

    # ----- 查询报价（多渠道对比） -----
    def query_price(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = PriceQueryRequest.model_validate(payload)
        result = self.provider.query_price(request)
        return {"status": "success", **result}

    # ----- 查询渠道 -----
    def query_channels(self) -> dict[str, Any]:
        result = self.provider.query_channels()
        return {"status": "success", **result}

    # ----- 查询目的地 -----
    def query_destinations(self, payload: dict[str, Any]) -> dict[str, Any]:
        params = DestQueryParams.model_validate(payload)
        result = self.provider.query_destinations(params)
        return {"status": "success", **result}

    # ----- 查询运单费用 -----
    def get_order_fees(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = OrderFeesRequest.model_validate(payload)
        result = self.provider.get_order_fees(request)
        return {"status": "success", **result}

    # ----- 删除运单 -----
    def delete_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = DeleteOrderRequest.model_validate(payload)
        result = self.provider.delete_order(request)
        return {"status": "success", **result}

    # ----- 错误格式化 -----
    @staticmethod
    def format_error(exc: Exception) -> dict[str, Any]:
        if isinstance(exc, OrderNotFoundError):
            return {
                "status": "error",
                "error": {
                    "code": "ORDER_NOT_FOUND",
                    "message": str(exc),
                    "retriable": False,
                },
            }
        if hasattr(exc, "errors"):
            return {
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "输入参数校验失败",
                    "details": exc.errors(),  # type: ignore[union-attr]
                    "retriable": False,
                },
            }
        # Remote API errors
        if hasattr(exc, "api_code"):
            return {
                "status": "error",
                "error": {
                    "code": "API_ERROR",
                    "message": str(exc),
                    "retriable": True,
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
