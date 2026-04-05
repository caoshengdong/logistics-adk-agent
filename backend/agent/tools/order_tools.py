"""Order lifecycle tools: create, query, delete."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from google.adk.tools import ToolContext

from agent.services.logistics_service import LogisticsService
from agent.tools._common import resolve_service


def _save_state(tool_context: ToolContext | None, key: str, value: Any) -> None:
    """Write a value into ADK session state (for cross-agent context sharing)."""
    if tool_context is not None:
        tool_context.state[key] = value


def create_order(
    channelid: str, customernumber1: str, countrycode: str,
    consigneename: str, consigneeaddress1: str, consigneecity: str,
    consigneezipcode: str, consigneeprovince: str,
    forecastweight: float, goods_cnname: str, goods_weight_kg: float,
    goods_quantity: int = 1, number: int = 1, isbattery: int = 0,
    goodstypecode: str = "WPX", consigneetel: str = "", note: str = "",
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Create a new logistics order (运单) and submit it to forecast status.
    Args:
        channelid: Shipping channel code, e.g. "FEDEX-IP", "DHL-EXPRESS".
        customernumber1: Customer reference number (客户参考号1), must be unique.
        countrycode: Destination country ISO code, e.g. "US", "GB", "JP".
        consigneename: Recipient name (收件人名称).
        consigneeaddress1: Recipient address line 1 (收件人地址).
        consigneecity: Recipient city (收件人城市).
        consigneezipcode: Recipient postal code (收件人邮编).
        consigneeprovince: Recipient state/province (收件人省州).
        forecastweight: Total forecast weight in KG (预报总重量).
        goods_cnname: Goods Chinese name (物品中文名), e.g. "手机壳".
        goods_weight_kg: Single item net weight in KG.
        goods_quantity: Quantity of goods.
        number: Total number of packages (总件数).
        isbattery: Whether contains battery (0=no, 1=yes).
        goodstypecode: Goods type code (WPX=包裹, DOC=文件, PAK=PAK袋).
        consigneetel: Recipient phone number.
        note: Order remark.
    """
    try:
        result = resolve_service(tool_context).create_order({
            "channelid": channelid, "customernumber1": customernumber1,
            "countrycode": countrycode, "consigneename": consigneename,
            "consigneeaddress1": consigneeaddress1,
            "consigneecity": consigneecity, "consigneezipcode": consigneezipcode,
            "consigneeprovince": consigneeprovince,
            "forecastweight": forecastweight, "number": number,
            "isbattery": isbattery, "goodstypecode": goodstypecode,
            "consigneetel": consigneetel, "note": note,
            "items": [
                {"cnname": goods_cnname, "weight": goods_weight_kg, "quantity": goods_quantity},
            ],
        })
        # ── Compress into state for follow-up turns ──
        if result.get("status") == "success" and result.get("data"):
            item = result["data"][0]
            _save_state(tool_context, "last_waybill", item.get("waybillnumber", ""))
            _save_state(tool_context, "last_order_channel", channelid)
            _save_state(tool_context, "last_order_destination", countrycode)
            _save_state(tool_context, "last_order_status", "Predicted")
            _save_state(tool_context, "last_order_recipient", consigneename)
            # New order invalidates any cached order list
            _save_state(tool_context, "last_orders_summary", "")
        return result
    except Exception as exc:
        return LogisticsService.format_error(exc)


def query_orders(
    begcreatedate: str = "", endcreatedate: str = "",
    page: int = 1, limit: int = 10,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Query orders by creation date range with pagination (分页查询运单).

    When the user asks for "recent orders" without specifying dates, you can
    call this tool WITHOUT providing begcreatedate/endcreatedate — it will
    automatically default to the last 14 days.

    Args:
        begcreatedate: Start date "YYYY-MM-DD HH:MM:SS". Defaults to 14 days ago if empty.
        endcreatedate: End date "YYYY-MM-DD HH:MM:SS". Defaults to now if empty.
        page: Page number starting from 1.
        limit: Number of orders per page (max 100).
    """
    now = datetime.now(tz=timezone.utc)
    if not endcreatedate:
        endcreatedate = now.strftime("%Y-%m-%d %H:%M:%S")
    if not begcreatedate:
        begcreatedate = (now - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    try:
        result = resolve_service(tool_context).query_orders({
            "begcreatedate": begcreatedate, "endcreatedate": endcreatedate,
            "page": page, "limit": limit,
        })
        # ── Compress into state: compact order summary ──
        if result.get("status") == "success":
            orders = result.get("data", [])
            summary = [
                f"{o.get('waybillnumber','?')}|{o.get('statusname','?')}|{o.get('countrycode','?')}"
                for o in orders[:10]
            ]
            _save_state(tool_context, "last_orders_summary",
                        f"{result.get('count', 0)} orders: " + ", ".join(summary))
        return result
    except Exception as exc:
        return LogisticsService.format_error(exc)


def delete_order(
    number: str, number_type: str = "customernumber",
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Delete an unshipped order. Only draft or forecast status can be deleted (删除运单).
    Args:
        number: The order number to delete.
        number_type: "customernumber", "waybillnumber", or "systemnumber".
    """
    try:
        result = resolve_service(tool_context).delete_order({number_type: number})
        # ── Clear stale order state so follow-ups don't reference the
        #    deleted order (e.g. "track it" after deletion). ──
        if result.get("status") == "success":
            _save_state(tool_context, "last_waybill", "")
            _save_state(tool_context, "last_order_channel", "")
            _save_state(tool_context, "last_order_destination", "")
            _save_state(tool_context, "last_order_status", "")
            _save_state(tool_context, "last_order_recipient", "")
            # Deletion invalidates the cached order list
            _save_state(tool_context, "last_orders_summary", "")
        return result
    except Exception as exc:
        return LogisticsService.format_error(exc)
