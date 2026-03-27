import pytest
from pydantic import ValidationError

from logistics_agent.models.domain import CreateShipmentRequest, RateQuoteRequest


def test_create_shipment_request_rejects_invalid_mode() -> None:
    with pytest.raises(ValidationError):
        CreateShipmentRequest(
            origin="Shenzhen, CN",
            destination="Los Angeles, US",
            weight_kg=10,
            goods_description="Shoes",
            mode="balloon",
        )



def test_rate_quote_rejects_non_positive_weight() -> None:
    with pytest.raises(ValidationError):
        RateQuoteRequest(
            origin="Shenzhen, CN",
            destination="Los Angeles, US",
            weight_kg=0,
            mode="air",
        )
