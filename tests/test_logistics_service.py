from logistics_agent.providers.mock_provider import MockLogisticsProvider
from logistics_agent.services.logistics_service import LogisticsService


provider = MockLogisticsProvider()
service = LogisticsService(provider=provider)


def test_track_existing_order() -> None:
    result = service.track_order("12345")
    assert result["status"] == "success"
    assert result["shipment"]["status"] == "in_transit"
    assert result["summary"]["shipment_id"] == "SHP-10001"



def test_create_shipment() -> None:
    result = service.create_shipment(
        {
            "origin": "Shenzhen, CN",
            "destination": "Los Angeles, US",
            "weight_kg": 12,
            "goods_description": "Footwear",
            "mode": "air",
            "order_id": "NEW-1",
        }
    )
    assert result["status"] == "success"
    assert result["shipment"]["order_id"] == "NEW-1"



def test_quote_rate() -> None:
    result = service.quote_rate(
        {
            "origin": "Shenzhen, CN",
            "destination": "Los Angeles, US",
            "weight_kg": 10,
            "mode": "sea",
        }
    )
    assert result["status"] == "success"
    assert result["quote"]["currency"] == "USD"



def test_format_validation_error_is_structured() -> None:
    try:
        service.quote_rate(
            {
                "origin": "Shenzhen, CN",
                "destination": "Los Angeles, US",
                "weight_kg": -1,
                "mode": "sea",
            }
        )
    except Exception as exc:
        result = service.format_error(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected validation error")
    assert result["status"] == "error"
    assert result["error"]["code"] == "VALIDATION_ERROR"



def test_format_internal_error() -> None:
    result = service.format_error(Exception("boom"))
    assert result["status"] == "error"
    assert result["error"]["code"] == "INTERNAL_ERROR"
