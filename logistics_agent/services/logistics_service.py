from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from logistics_agent.models.domain import (
    ChannelPriceRequest,
    CreateOrderRequest,
    DeleteOrderRequest,
    DestQueryParams,
    LogisticsApiError,
    OrderFeesRequest,
    OrderNotFoundError,
    PriceQueryRequest,
    QueryOrdersRequest,
    TrackRequest,
)
from logistics_agent.providers.base import LogisticsProvider

logger = logging.getLogger(__name__)


@dataclass
class LogisticsService:
    provider: LogisticsProvider

    # ----- 下单 -----
    def create_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = CreateOrderRequest.model_validate(payload)
        logger.info("create_order channel=%s customer_ref=%s", request.channelid, request.customernumber1)
        result = self.provider.create_order(request)
        return {"status": "success", **result}

    # ----- 查询运单 -----
    def query_orders(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = QueryOrdersRequest.model_validate(payload)
        logger.info("query_orders range=[%s, %s] page=%d", request.begcreatedate, request.endcreatedate, request.page)
        result = self.provider.query_orders(request)
        return {"status": "success", **result}

    # ----- 轨迹追踪 -----
    def track_shipment(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = TrackRequest.model_validate(payload)
        logger.info("track_shipment payload=%s", payload)
        result = self.provider.track_shipment(request)
        return {"status": "success", **result}

    # ----- 运费试算（指定渠道） -----
    def estimate_channel_price(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = ChannelPriceRequest.model_validate(payload)
        logger.info("estimate_channel_price channel=%s country=%s weight=%s", request.channelid, request.countrycode, request.forecastweight)
        result = self.provider.estimate_channel_price(request)
        return {"status": "success", **result}

    # ----- 查询报价（多渠道对比） -----
    def query_price(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = PriceQueryRequest.model_validate(payload)
        logger.info("query_price dest=%s weight=%s", request.dest, request.weight)
        result = self.provider.query_price(request)
        return {"status": "success", **result}

    # ----- 查询渠道 -----
    def query_channels(self) -> dict[str, Any]:
        logger.info("query_channels")
        result = self.provider.query_channels()
        return {"status": "success", **result}

    # ----- 查询目的地 -----
    def query_destinations(self, payload: dict[str, Any]) -> dict[str, Any]:
        params = DestQueryParams.model_validate(payload)
        logger.info("query_destinations type=%s keyword=%s", params.desttype, params.dest)
        result = self.provider.query_destinations(params)
        return {"status": "success", **result}

    # ----- 查询运单费用 -----
    def get_order_fees(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = OrderFeesRequest.model_validate(payload)
        logger.info("get_order_fees waybills=%s", request.waybillnumber)
        result = self.provider.get_order_fees(request)
        return {"status": "success", **result}

    # ----- 删除运单 -----
    def delete_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = DeleteOrderRequest.model_validate(payload)
        logger.info("delete_order payload=%s", payload)
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
        from pydantic import ValidationError
        if isinstance(exc, ValidationError):
            return {
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Parameter validation failed",
                    "details": exc.errors(),
                    "retriable": False,
                },
            }
        if isinstance(exc, LogisticsApiError):
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
