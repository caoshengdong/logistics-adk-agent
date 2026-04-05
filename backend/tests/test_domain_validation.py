import pytest
from pydantic import ValidationError

from agent.models.domain import (
    ChannelPriceRequest,
    CreateOrderRequest,
    PriceQueryRequest,
    QueryOrdersRequest,
    TrackRequest,
)


def test_create_order_request_validates_required_fields() -> None:
    """Missing required fields should raise ValidationError."""
    with pytest.raises(ValidationError):
        CreateOrderRequest()  # type: ignore[call-arg]


def test_create_order_request_rejects_zero_weight() -> None:
    with pytest.raises(ValidationError):
        CreateOrderRequest(
            channelid="FEDEX-IP",
            customernumber1="TEST-001",
            countrycode="US",
            consigneename="John",
            consigneeaddress1="123 Main St",
            consigneecity="LA",
            consigneezipcode="90001",
            consigneeprovince="CA",
            forecastweight=0,  # must be > 0
        )


def test_create_order_request_uppercases_country() -> None:
    req = CreateOrderRequest(
        channelid="FEDEX-IP",
        customernumber1="TEST-002",
        countrycode="us",
        consigneename="John",
        consigneeaddress1="123 Main St",
        consigneecity="LA",
        consigneezipcode="90001",
        consigneeprovince="CA",
        forecastweight=5.0,
    )
    assert req.countrycode == "US"


def test_channel_price_request_rejects_empty_channelid() -> None:
    with pytest.raises(ValidationError):
        ChannelPriceRequest(
            channelid="",
            forecastweight=10.0,
            countrycode="US",
        )


def test_price_query_request_rejects_zero_weight() -> None:
    with pytest.raises(ValidationError):
        PriceQueryRequest(dest="US", weight=0)


def test_track_request_wraps_single_string() -> None:
    req = TrackRequest(waybillnumber="ABC123")
    assert req.waybillnumber == ["ABC123"]


def test_query_orders_request_rejects_zero_page() -> None:
    with pytest.raises(ValidationError):
        QueryOrdersRequest(
            begcreatedate="2026-01-01 00:00:00",
            endcreatedate="2026-12-31 23:59:59",
            page=0,
        )
