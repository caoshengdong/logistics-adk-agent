"""Tests for tool-layer functions.

Each tool is tested through its public interface with a mocked service,
verifying argument pass-through and error handling.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent.services.logistics_service import LogisticsService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_service() -> MagicMock:
    svc = MagicMock(spec=LogisticsService)
    svc.create_order.return_value = {"code": 0, "msg": "ok"}
    svc.query_orders.return_value = {"code": 0, "count": 0, "data": []}
    svc.delete_order.return_value = {"code": 0, "msg": "deleted"}
    svc.track_shipment.return_value = {"code": 0, "data": []}
    svc.get_order_fees.return_value = {"code": 0, "data": []}
    svc.estimate_channel_price.return_value = {"code": 0, "data": []}
    svc.query_price.return_value = {"code": 0, "data": []}
    svc.query_channels.return_value = {"code": 0, "data": []}
    svc.query_destinations.return_value = {"code": 0, "data": []}
    svc.format_error = LogisticsService.format_error
    return svc


# ---------------------------------------------------------------------------
# order_tools
# ---------------------------------------------------------------------------

class TestOrderTools:
    @patch("agent.tools.order_tools.resolve_service")
    def test_create_order_passes_args(self, mock_resolve: MagicMock):
        svc = _mock_service()
        mock_resolve.return_value = svc

        from agent.tools.order_tools import create_order
        create_order(
            channelid="FEDEX-IP",
            customernumber1="REF-001",
            countrycode="US",
            consigneename="John",
            consigneeaddress1="123 Main St",
            consigneecity="NYC",
            consigneezipcode="10001",
            consigneeprovince="NY",
            forecastweight=5.0,
            goods_cnname="手机壳",
            goods_weight_kg=2.5,
        )
        svc.create_order.assert_called_once()
        payload = svc.create_order.call_args[0][0]
        assert payload["channelid"] == "FEDEX-IP"
        assert payload["countrycode"] == "US"
        assert payload["items"][0]["cnname"] == "手机壳"

    @patch("agent.tools.order_tools.resolve_service")
    def test_create_order_handles_exception(self, mock_resolve: MagicMock):
        svc = _mock_service()
        svc.create_order.side_effect = ValueError("boom")
        mock_resolve.return_value = svc

        from agent.tools.order_tools import create_order
        result = create_order(
            channelid="X", customernumber1="X", countrycode="US",
            consigneename="X", consigneeaddress1="X", consigneecity="X",
            consigneezipcode="X", consigneeprovince="X",
            forecastweight=1.0, goods_cnname="X", goods_weight_kg=1.0,
        )
        assert result["status"] == "error"

    @patch("agent.tools.order_tools.resolve_service")
    def test_query_orders_passes_date_range(self, mock_resolve: MagicMock):
        svc = _mock_service()
        mock_resolve.return_value = svc

        from agent.tools.order_tools import query_orders
        query_orders(begcreatedate="2026-01-01 00:00:00", endcreatedate="2026-12-31 23:59:59")
        payload = svc.query_orders.call_args[0][0]
        assert payload["begcreatedate"] == "2026-01-01 00:00:00"
        assert payload["limit"] == 10  # default

    @patch("agent.tools.order_tools.resolve_service")
    def test_query_orders_defaults_to_last_14_days(self, mock_resolve: MagicMock):
        svc = _mock_service()
        mock_resolve.return_value = svc

        from datetime import datetime, timezone

        from agent.tools.order_tools import query_orders
        query_orders()  # no dates provided
        payload = svc.query_orders.call_args[0][0]
        # Should have auto-filled dates
        beg = datetime.strptime(payload["begcreatedate"], "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(payload["endcreatedate"], "%Y-%m-%d %H:%M:%S")
        diff = (end - beg).days
        assert 13 <= diff <= 14  # roughly 14 days
        assert payload["limit"] == 10

    @patch("agent.tools.order_tools.resolve_service")
    def test_delete_order_passes_number(self, mock_resolve: MagicMock):
        svc = _mock_service()
        mock_resolve.return_value = svc

        from agent.tools.order_tools import delete_order
        delete_order(number="WB-001", number_type="waybillnumber")
        svc.delete_order.assert_called_once_with({"waybillnumber": "WB-001"})


# ---------------------------------------------------------------------------
# tracking_tools
# ---------------------------------------------------------------------------

class TestTrackingTools:
    @patch("agent.tools.tracking_tools.resolve_service")
    def test_track_shipment_by_waybill(self, mock_resolve: MagicMock):
        svc = _mock_service()
        mock_resolve.return_value = svc

        from agent.tools.tracking_tools import track_shipment
        track_shipment(number="T6W001", number_type="waybillnumber")
        svc.track_shipment.assert_called_once_with({"waybillnumber": ["T6W001"]})

    @patch("agent.tools.tracking_tools.resolve_service")
    def test_track_shipment_by_customer(self, mock_resolve: MagicMock):
        svc = _mock_service()
        mock_resolve.return_value = svc

        from agent.tools.tracking_tools import track_shipment
        track_shipment(number="CUST-001", number_type="customernumber")
        svc.track_shipment.assert_called_once_with({"customernumber": ["CUST-001"]})

    @patch("agent.tools.tracking_tools.resolve_service")
    def test_get_order_fees_passes_waybill(self, mock_resolve: MagicMock):
        svc = _mock_service()
        mock_resolve.return_value = svc

        from agent.tools.tracking_tools import get_order_fees
        get_order_fees(waybillnumber="T6W001")
        svc.get_order_fees.assert_called_once_with({"waybillnumber": ["T6W001"]})

    @patch("agent.tools.tracking_tools.resolve_service")
    def test_track_shipment_handles_exception(self, mock_resolve: MagicMock):
        svc = _mock_service()
        svc.track_shipment.side_effect = RuntimeError("timeout")
        mock_resolve.return_value = svc

        from agent.tools.tracking_tools import track_shipment
        result = track_shipment(number="X")
        assert result["status"] == "error"
        assert result["error"]["code"] == "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# pricing_tools
# ---------------------------------------------------------------------------

class TestPricingTools:
    @patch("agent.tools.pricing_tools.resolve_service")
    def test_estimate_shipping_cost_passes_args(self, mock_resolve: MagicMock):
        svc = _mock_service()
        mock_resolve.return_value = svc

        from agent.tools.pricing_tools import estimate_shipping_cost
        estimate_shipping_cost(channelid="DHL-EXPRESS", countrycode="GB", forecastweight=3.0)
        payload = svc.estimate_channel_price.call_args[0][0]
        assert payload["channelid"] == "DHL-EXPRESS"
        assert payload["forecastweight"] == 3.0

    @patch("agent.tools.pricing_tools.resolve_service")
    def test_query_price_passes_args(self, mock_resolve: MagicMock):
        svc = _mock_service()
        mock_resolve.return_value = svc

        from agent.tools.pricing_tools import query_price
        query_price(dest="US", weight=10.0, piece=2)
        payload = svc.query_price.call_args[0][0]
        assert payload["dest"] == "US"
        assert payload["weight"] == 10.0
        assert payload["piece"] == 2

    @patch("agent.tools.pricing_tools.resolve_service")
    def test_query_channels_no_args(self, mock_resolve: MagicMock):
        svc = _mock_service()
        mock_resolve.return_value = svc

        from agent.tools.pricing_tools import query_channels
        query_channels()
        svc.query_channels.assert_called_once()

    @patch("agent.tools.pricing_tools.resolve_service")
    def test_query_destinations_default(self, mock_resolve: MagicMock):
        svc = _mock_service()
        mock_resolve.return_value = svc

        from agent.tools.pricing_tools import query_destinations
        query_destinations()
        payload = svc.query_destinations.call_args[0][0]
        assert payload["desttype"] == "country"
        assert payload["dest"] == ""

    @patch("agent.tools.pricing_tools.resolve_service")
    def test_estimate_handles_exception(self, mock_resolve: MagicMock):
        svc = _mock_service()
        svc.estimate_channel_price.side_effect = ConnectionError("refused")
        mock_resolve.return_value = svc

        from agent.tools.pricing_tools import estimate_shipping_cost
        result = estimate_shipping_cost(channelid="X", countrycode="US", forecastweight=1.0)
        assert result["status"] == "error"

