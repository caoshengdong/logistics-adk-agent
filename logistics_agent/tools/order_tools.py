"""Order lifecycle tools: create, query, delete."""
from __future__ import annotations

from typing import Any

from google.adk.tools import ToolContext

from logistics_agent.services.logistics_service import LogisticsService
from logistics_agent.tools._common import resolve_service


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
        return resolve_service(tool_context).create_order({
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
    except Exception as exc:
        return LogisticsService.format_error(exc)


def query_orders(
    begcreatedate: str, endcreatedate: str, page: int = 1, limit: int = 10,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Query orders by creation date range with pagination (分页查询运单).
    Args:
        begcreatedate: Start date "YYYY-MM-DD HH:MM:SS".
        endcreatedate: End date "YYYY-MM-DD HH:MM:SS".
        page: Page number starting from 1.
        limit: Number of orders per page (max 100).
    """
    try:
        return resolve_service(tool_context).query_orders({
            "begcreatedate": begcreatedate, "endcreatedate": endcreatedate,
            "page": page, "limit": limit,
        })
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
        return resolve_service(tool_context).delete_order({number_type: number})
    except Exception as exc:
        return LogisticsService.format_error(exc)
