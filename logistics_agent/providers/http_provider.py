"""HTTP provider for the logistics system API (跨境物流系统).

Uses httpx for transport.  Every POST endpoint follows the convention::

    {
        "authorization": {"code": "<client_code>", "token": "<api_token>"},
        "datas": { ... }
    }
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from logistics_agent.models.domain import (
    ChannelPriceRequest,
    CreateOrderRequest,
    DeleteOrderRequest,
    DestQueryParams,
    LogisticsApiError,
    OrderFeesRequest,
    PriceQueryRequest,
    QueryOrdersRequest,
    TrackRequest,
)
from logistics_agent.providers.base import LogisticsProvider

logger = logging.getLogger(__name__)



@dataclass
class HttpLogisticsProvider(LogisticsProvider):
    base_url: str
    auth_code: str
    auth_token: str
    timeout_seconds: float = 10.0
    _client: httpx.Client = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            headers={"Content-Type": "application/json"},
        )

    def close(self) -> None:
        """Close the underlying httpx client and release connections."""
        self._client.close()

    def __enter__(self) -> HttpLogisticsProvider:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Transport helpers
    # ------------------------------------------------------------------

    def _auth_block(self) -> dict[str, str]:
        return {"code": self.auth_code, "token": self.auth_token}

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a POST with the standard authorization envelope."""
        body: dict[str, Any] = {"authorization": self._auth_block()}
        body.update(payload)
        logger.debug("POST %s body=%s", path, body)
        resp = self._client.post(path, json=body)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        if data.get("code") not in (0, "0", None):
            raise LogisticsApiError(data.get("code", -1), data.get("msg", "unknown"))
        return data

    def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        logger.debug("GET %s params=%s", path, params)
        resp = self._client.get(path, params=params)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return data

    # ------------------------------------------------------------------
    # Provider interface
    # ------------------------------------------------------------------

    def create_order(self, request: CreateOrderRequest) -> dict[str, Any]:
        order_data = request.model_dump(mode="json", exclude_defaults=True)
        # Split items / volumes out of order block per API schema
        items = order_data.pop("items", [])
        volumes = order_data.pop("volumes", [])
        entry: dict[str, Any] = {"order": order_data}
        if items:
            entry["items"] = items
        if volumes:
            entry["volumes"] = volumes
        return self._post("/api/order/createForecast", {"datas": [entry]})

    def query_orders(self, request: QueryOrdersRequest) -> dict[str, Any]:
        return self._post("/api/order/pageOrders", {
            "page": {"page": request.page, "limit": request.limit},
            "datas": {
                "datatype": request.datatype,
                "begcreatedate": request.begcreatedate,
                "endcreatedate": request.endcreatedate,
            },
        })

    def track_shipment(self, request: TrackRequest) -> dict[str, Any]:
        datas: dict[str, Any] = {}
        if request.waybillnumber:
            datas["waybillnumber"] = request.waybillnumber
        elif request.systemnumber:
            datas["systemnumber"] = request.systemnumber
        elif request.customernumber:
            datas["customernumber"] = request.customernumber
        return self._post("/api/track", {"datas": datas})

    def estimate_channel_price(self, request: ChannelPriceRequest) -> dict[str, Any]:
        order_data = request.model_dump(mode="json", exclude_defaults=True)
        # searchChannelPrice reuses the create-order shape inside datas[]
        # Fill in all required fields that the simplified tool doesn't expose
        order_data.setdefault("consigneename", "试算用户")
        order_data.setdefault("consigneeaddress1", "Test Address")
        order_data.setdefault("consigneeprovince", "N/A")
        order_data.setdefault("ismagnet", 0)
        order_data.setdefault("isliquid", 0)
        order_data.setdefault("ispowder", 0)
        order_data.setdefault("packagetypecode", "O")
        return self._post("/api/searchChannelPrice", {
            "datas": [{"order": order_data}],
        })

    def query_price(self, request: PriceQueryRequest) -> dict[str, Any]:
        datas = request.model_dump(mode="json", exclude_defaults=True)
        return self._post("/api/searchPrice", {"datas": datas})

    def query_channels(self) -> dict[str, Any]:
        return self._post("/api/order/channel", {})

    def query_destinations(self, params: DestQueryParams) -> dict[str, Any]:
        return self._get("/api/searchDest", {
            "desttype": params.desttype,
            "dest": params.dest,
        })

    def get_order_fees(self, request: OrderFeesRequest) -> dict[str, Any]:
        return self._post("/api/order/recsheet", {
            "datas": {"waybillnumber": request.waybillnumber or []},
        })

    def delete_order(self, request: DeleteOrderRequest) -> dict[str, Any]:
        datas: dict[str, str] = {}
        if request.customernumber:
            datas["customernumber"] = request.customernumber
        elif request.waybillnumber:
            datas["waybillnumber"] = request.waybillnumber
        elif request.systemnumber:
            datas["systemnumber"] = request.systemnumber
        return self._post("/api/order/delete", {"datas": datas})
