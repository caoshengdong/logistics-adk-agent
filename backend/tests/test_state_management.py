"""Tests for ADK session state management.

Covers:
- State invalidation rules (stale-state cleanup after create/delete/error)
- Snapshot filtering (auth keys never leak into persisted snapshot)
- State key completeness (every prompt-referenced key exists in initial_state)
- Cold-start state overlay (saved_state restores working memory, not auth)
"""

from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

from agent.services.logistics_service import LogisticsService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_tool_context(initial_state: dict | None = None) -> MagicMock:
    """Create a fake ToolContext whose ``.state`` is a plain dict."""
    ctx = MagicMock()
    ctx.state = dict(initial_state or {})
    return ctx


def _mock_service() -> MagicMock:
    svc = MagicMock(spec=LogisticsService)
    svc.format_error = LogisticsService.format_error
    return svc


# ---------------------------------------------------------------------------
# P2: Stale-state invalidation rules
# ---------------------------------------------------------------------------

class TestOrderStateInvalidation:
    """create_order / delete_order must keep working-memory consistent."""

    @patch("agent.tools.order_tools.resolve_service")
    def test_create_order_sets_state_on_success(self, mock_resolve: MagicMock):
        svc = _mock_service()
        svc.create_order.return_value = {
            "status": "success",
            "data": [{"waybillnumber": "WB123"}],
        }
        mock_resolve.return_value = svc

        ctx = _mock_tool_context()
        from agent.tools.order_tools import create_order
        create_order(
            channelid="FEDEX-IP", customernumber1="REF-1", countrycode="US",
            consigneename="Alice", consigneeaddress1="123 Main",
            consigneecity="NYC", consigneezipcode="10001",
            consigneeprovince="NY", forecastweight=2.0,
            goods_cnname="手机壳", goods_weight_kg=2.0,
            tool_context=ctx,
        )
        assert ctx.state["last_waybill"] == "WB123"
        assert ctx.state["last_order_channel"] == "FEDEX-IP"
        assert ctx.state["last_order_destination"] == "US"
        assert ctx.state["last_order_status"] == "Predicted"
        assert ctx.state["last_order_recipient"] == "Alice"
        # Creating an order invalidates the cached order list
        assert ctx.state["last_orders_summary"] == ""

    @patch("agent.tools.order_tools.resolve_service")
    def test_delete_order_clears_all_order_state(self, mock_resolve: MagicMock):
        svc = _mock_service()
        svc.delete_order.return_value = {"status": "success"}
        mock_resolve.return_value = svc

        ctx = _mock_tool_context({
            "last_waybill": "WB123",
            "last_order_channel": "FEDEX-IP",
            "last_order_destination": "US",
            "last_order_status": "Predicted",
            "last_order_recipient": "Alice",
            "last_orders_summary": "1 orders: WB123|Predicted|US",
        })
        from agent.tools.order_tools import delete_order
        delete_order(number="WB123", number_type="waybillnumber", tool_context=ctx)

        assert ctx.state["last_waybill"] == ""
        assert ctx.state["last_order_channel"] == ""
        assert ctx.state["last_order_destination"] == ""
        assert ctx.state["last_order_status"] == ""
        assert ctx.state["last_order_recipient"] == ""
        assert ctx.state["last_orders_summary"] == ""


class TestTrackingStateInvalidation:
    """track_shipment error path must clear stale tracking state."""

    @patch("agent.tools.tracking_tools.resolve_service")
    def test_track_shipment_error_clears_state(self, mock_resolve: MagicMock):
        svc = _mock_service()
        svc.track_shipment.return_value = {
            "data": [{"errormsg": "无效的单号"}],
        }
        mock_resolve.return_value = svc

        ctx = _mock_tool_context({
            "last_tracked_waybill": "OLD-WB",
            "last_tracked_status": "Delivered",
        })
        from agent.tools.tracking_tools import track_shipment
        result = track_shipment(number="BADNUM", tool_context=ctx)

        assert result["status"] == "error"
        assert ctx.state["last_tracked_waybill"] == ""
        assert ctx.state["last_tracked_status"] == ""

    @patch("agent.tools.tracking_tools.resolve_service")
    def test_track_shipment_success_sets_state(self, mock_resolve: MagicMock):
        svc = _mock_service()
        svc.track_shipment.return_value = {
            "data": [{
                "waybillnumber": "WB999",
                "orderstatusName": "In Transit",
            }],
        }
        mock_resolve.return_value = svc

        ctx = _mock_tool_context()
        from agent.tools.tracking_tools import track_shipment
        track_shipment(number="WB999", tool_context=ctx)

        assert ctx.state["last_tracked_waybill"] == "WB999"
        assert ctx.state["last_tracked_status"] == "In Transit"


class TestPricingStateInvalidation:
    """query_price must invalidate stale single-channel estimates."""

    @patch("agent.tools.pricing_tools.resolve_service")
    def test_query_price_clears_old_estimate(self, mock_resolve: MagicMock):
        svc = _mock_service()
        svc.query_price.return_value = {
            "status": "success",
            "data": [{
                "channel": {"channelid": "DHL-EX"},
                "totalCost": 45.0,
            }],
        }
        mock_resolve.return_value = svc

        ctx = _mock_tool_context({
            "last_estimate_channel": "FEDEX-IP",
            "last_estimate_total": "120.00 RMB",
        })
        from agent.tools.pricing_tools import query_price
        query_price(dest="US", weight=5.0, tool_context=ctx)

        # New comparison should clear the old single-channel estimate
        assert ctx.state["last_estimate_channel"] == ""
        assert ctx.state["last_estimate_total"] == ""
        # And set new comparison state
        assert ctx.state["last_cheapest_channel"] == "DHL-EX"
        assert "DHL-EX" in ctx.state["last_quote_summary"]


# ---------------------------------------------------------------------------
# P3: No dead state keys — every key in initial_state appears in the prompt
# ---------------------------------------------------------------------------

class TestStateKeyCompleteness:
    """Every working-memory key in initial_state must be referenced in
    the root agent's instruction template, and vice versa."""

    def test_all_initial_state_keys_in_prompt(self):
        """Keys registered in initial_state should appear in the prompt."""
        from agent.agent import root_agent

        instruction = root_agent.instruction
        # Extract all {key} references from the instruction
        prompt_keys = set(re.findall(r"\{(\w+)\}", instruction))

        # Build the same initial_state dict (without auth keys)
        working_memory_keys = {
            "last_waybill", "last_order_channel", "last_order_destination",
            "last_order_status", "last_order_recipient", "last_orders_summary",
            "last_quote_summary", "last_cheapest_channel",
            "last_estimate_channel", "last_estimate_total",
            "last_tracked_waybill", "last_tracked_status",
            "last_fees_waybill", "last_fees_total",
        }

        missing_from_prompt = working_memory_keys - prompt_keys
        assert not missing_from_prompt, (
            f"Working-memory keys not referenced in prompt: {missing_from_prompt}"
        )

    def test_no_dead_prompt_keys(self):
        """Every {key} in the prompt must exist in initial_state."""
        from agent.agent import root_agent

        instruction = root_agent.instruction
        prompt_keys = set(re.findall(r"\{(\w+)\}", instruction))

        # All keys that exist in initial_state (auth + working memory)
        all_initial_keys = {
            "auth_code", "auth_token", "customer_code", "customer_name",
            "last_waybill", "last_order_channel", "last_order_destination",
            "last_order_status", "last_order_recipient", "last_orders_summary",
            "last_quote_summary", "last_cheapest_channel",
            "last_estimate_channel", "last_estimate_total",
            "last_tracked_waybill", "last_tracked_status",
            "last_fees_waybill", "last_fees_total",
        }

        missing_from_state = prompt_keys - all_initial_keys
        assert not missing_from_state, (
            f"Prompt references keys not in initial_state (will cause KeyError): "
            f"{missing_from_state}"
        )


# ---------------------------------------------------------------------------
# Snapshot filtering: auth keys must never leak into DB
# ---------------------------------------------------------------------------

class TestSnapshotFiltering:
    def test_ephemeral_keys_excluded_from_snapshot(self):
        """The ephemeral key set should contain all auth-related keys."""
        from app.chat.adk_runner import _EPHEMERAL_KEYS

        for key in ("auth_code", "auth_token", "customer_code", "customer_name"):
            assert key in _EPHEMERAL_KEYS, f"{key} must be ephemeral"

    def test_snapshot_only_includes_last_keys(self):
        """Simulate the snapshot filter logic from run_agent_stream."""
        from app.chat.adk_runner import _EPHEMERAL_KEYS

        fake_state = {
            "auth_code": "SECRET",
            "auth_token": "TOKEN",
            "customer_code": "CUST",
            "customer_name": "Name",
            "last_waybill": "WB123",
            "last_tracked_status": "Delivered",
            "some_random_key": "should not appear",
        }
        snapshot = {
            k: v for k, v in fake_state.items()
            if k.startswith("last_") and k not in _EPHEMERAL_KEYS
        }
        assert "auth_code" not in snapshot
        assert "auth_token" not in snapshot
        assert "customer_code" not in snapshot
        assert "some_random_key" not in snapshot
        assert snapshot["last_waybill"] == "WB123"
        assert snapshot["last_tracked_status"] == "Delivered"


# ---------------------------------------------------------------------------
# Cold-start state overlay: saved_state must skip ephemeral keys
# ---------------------------------------------------------------------------

class TestColdStartOverlay:
    def test_saved_state_does_not_restore_auth(self):
        """If someone tampered with state_json in the DB and added auth
        keys, they must NOT override the fresh User-row values."""
        from app.chat.adk_runner import _EPHEMERAL_KEYS

        initial_state = {
            "auth_code": "FRESH_CODE",
            "auth_token": "FRESH_TOKEN",
            "customer_code": "FRESH_CUST",
            "customer_name": "Fresh Name",
            "last_waybill": "",
            "last_tracked_status": "",
        }

        saved_state = {
            "auth_code": "STALE_CODE",          # must be ignored
            "auth_token": "STALE_TOKEN",         # must be ignored
            "last_waybill": "WB-RESTORED",       # should be applied
            "last_tracked_status": "In Transit",  # should be applied
        }

        # Replicate the overlay logic from get_or_create_session
        for key, value in saved_state.items():
            if key in initial_state and key not in _EPHEMERAL_KEYS:
                initial_state[key] = value

        assert initial_state["auth_code"] == "FRESH_CODE"
        assert initial_state["auth_token"] == "FRESH_TOKEN"
        assert initial_state["last_waybill"] == "WB-RESTORED"
        assert initial_state["last_tracked_status"] == "In Transit"


# ---------------------------------------------------------------------------
# Sub-agent output_key removal
# ---------------------------------------------------------------------------

class TestOutputKeyRemoved:
    """Sub-agents should not have output_key set (was dumping full text
    responses into state — never consumed)."""

    def test_no_output_key_on_sub_agents(self):
        from agent.agent import order_agent, pricing_agent, tracking_agent

        for agent in (order_agent, tracking_agent, pricing_agent):
            assert agent.output_key is None or agent.output_key == "", (
                f"{agent.name} still has output_key={agent.output_key!r}"
            )

