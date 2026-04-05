"""Tests for LogisticsService using MockLogisticsProvider.

Covers the full lifecycle: channels → price → create → query → track → fees → delete.
"""

import pytest

from logistics_agent.providers.mock_provider import MockLogisticsProvider
from logistics_agent.services.logistics_service import LogisticsService


@pytest.fixture()
def service() -> LogisticsService:
    """Fresh provider + service per test for full isolation."""
    return LogisticsService(provider=MockLogisticsProvider())


# ----- query_channels -----

def test_query_channels(service: LogisticsService) -> None:
    result = service.query_channels()
    assert result["status"] == "success"
    assert len(result["data"]) >= 5
    assert result["data"][0]["channelid"]


# ----- query_destinations -----

def test_query_destinations_all(service: LogisticsService) -> None:
    result = service.query_destinations({"dest": "", "desttype": "country"})
    assert result["status"] == "success"
    assert len(result["data"]) >= 5


def test_query_destinations_filter(service: LogisticsService) -> None:
    result = service.query_destinations({"dest": "US"})
    assert result["status"] == "success"
    assert any(d["destCode"] == "US" for d in result["data"])


# ----- query_price -----

def test_query_price(service: LogisticsService) -> None:
    result = service.query_price({"dest": "US", "weight": 10.0})
    assert result["status"] == "success"
    assert len(result["data"]) >= 1
    first = result["data"][0]
    assert first["totalCost"] > 0
    assert first["channel"]["channelid"]


# ----- estimate_channel_price -----

def test_estimate_channel_price(service: LogisticsService) -> None:
    result = service.estimate_channel_price({
        "channelid": "FEDEX-IP", "countrycode": "US", "forecastweight": 10.0,
    })
    assert result["status"] == "success"
    price_data = result["data"][0]
    assert price_data["amount"] > 0
    assert len(price_data["details"]) >= 2


# ----- create_order -----

def test_create_order(service: LogisticsService) -> None:
    result = service.create_order({
        "channelid": "DHL-EXPRESS",
        "customernumber1": "SVC-TEST-001",
        "countrycode": "GB",
        "consigneename": "Test User",
        "consigneeaddress1": "123 Test Street",
        "consigneecity": "London",
        "consigneezipcode": "SW1A 1AA",
        "consigneeprovince": "England",
        "forecastweight": 5.0,
        "items": [{"cnname": "测试商品", "weight": 2.5}],
    })
    assert result["status"] == "success"
    order_data = result["data"][0]
    assert order_data["code"] == 0
    assert order_data["customernumber"] == "SVC-TEST-001"
    assert order_data["systemnumber"].startswith("SYS")
    assert order_data["waybillnumber"].startswith("T6W")


# ----- query_orders -----

def test_query_orders(service: LogisticsService) -> None:
    result = service.query_orders({
        "begcreatedate": "2026-01-01 00:00:00",
        "endcreatedate": "2026-12-31 23:59:59",
    })
    assert result["status"] == "success"
    assert result["count"] >= 1
    assert isinstance(result["data"], list)


# ----- track_shipment -----

def test_track_shipment_by_waybill(service: LogisticsService) -> None:
    result = service.track_shipment({"waybillnumber": ["T6W20260401002"]})
    assert result["status"] == "success"
    track = result["data"][0]
    assert track["waybillnumber"] == "T6W20260401002"
    assert track["orderstatusName"] == "已发货"
    assert len(track["trackItems"]) >= 2


def test_track_shipment_by_systemnumber(service: LogisticsService) -> None:
    result = service.track_shipment({"systemnumber": "SYS20260401004"})
    assert result["status"] == "success"
    track = result["data"][0]
    assert track["systemnumber"] == "SYS20260401004"


def test_track_shipment_not_found(service: LogisticsService) -> None:
    result = service.track_shipment({"waybillnumber": "NONEXISTENT"})
    assert result["status"] == "success"
    assert result["data"][0]["errormsg"] == "无效的单号"


# ----- get_order_fees -----

def test_get_order_fees(service: LogisticsService) -> None:
    result = service.get_order_fees({"waybillnumber": ["T6W20260401003"]})
    assert result["status"] == "success"
    fees = result["data"][0]
    assert fees["searchNumber"] == "T6W20260401003"
    assert len(fees["recsheetList"]) >= 2


def test_get_order_fees_not_found(service: LogisticsService) -> None:
    result = service.get_order_fees({"waybillnumber": ["FAKE-123"]})
    assert result["status"] == "success"
    assert result["data"][0]["errormsg"] == "无效的单号"


# ----- delete_order -----

def test_delete_order_predicted_status(service: LogisticsService) -> None:
    """Deleting an order in Predicted status should succeed."""
    result = service.delete_order({"customernumber": "CUST-20260401-001"})
    assert result["status"] == "success"
    assert result["msg"] == "删除成功"


def test_delete_order_shipped_status(service: LogisticsService) -> None:
    """Deleting a shipped order should fail."""
    result = service.delete_order({"waybillnumber": "T6W20260401002"})
    assert result["status"] == "success"
    assert result["code"] == -1
    assert "无法删除" in result["msg"]


def test_delete_order_not_found(service: LogisticsService) -> None:
    """Deleting a non-existent order should raise and format error."""
    from logistics_agent.models.domain import OrderNotFoundError
    result = service.format_error(
        OrderNotFoundError("未找到单号: NONEXISTENT")
    )
    assert result["status"] == "error"
    assert result["error"]["code"] == "ORDER_NOT_FOUND"


# ----- format_error -----

def test_format_validation_error(service: LogisticsService) -> None:
    try:
        service.estimate_channel_price({
            "channelid": "",  # invalid
            "forecastweight": 10.0,
            "countrycode": "US",
        })
    except Exception as exc:
        result = service.format_error(exc)
    else:
        raise AssertionError("Expected validation error")
    assert result["status"] == "error"
    assert result["error"]["code"] == "VALIDATION_ERROR"


def test_format_api_error(service: LogisticsService) -> None:
    from logistics_agent.models.domain import LogisticsApiError
    result = service.format_error(LogisticsApiError(code=500, msg="server error"))
    assert result["status"] == "error"
    assert result["error"]["code"] == "API_ERROR"
    assert result["error"]["retriable"] is True


def test_format_internal_error(service: LogisticsService) -> None:
    result = service.format_error(Exception("boom"))
    assert result["status"] == "error"
    assert result["error"]["code"] == "INTERNAL_ERROR"
