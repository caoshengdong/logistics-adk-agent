"""ADK Tool functions for the logistics agent.

Each function maps to one logistics system API capability. The docstrings are
consumed by the LLM to understand when and how to invoke each tool.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from logistics_agent.providers.factory import get_provider
from logistics_agent.services.logistics_service import LogisticsService


@lru_cache(maxsize=1)
def _service() -> LogisticsService:
    return LogisticsService(provider=get_provider())


# ---------------------------------------------------------------------------
# 1. 创建运单 (Create Order)
# ---------------------------------------------------------------------------

def create_order(
    channelid: str,
    customernumber1: str,
    countrycode: str,
    consigneename: str,
    consigneeaddress1: str,
    consigneecity: str,
    consigneezipcode: str,
    consigneeprovince: str,
    forecastweight: float,
    goods_cnname: str,
    goods_weight_kg: float,
    goods_quantity: int = 1,
    number: int = 1,
    isbattery: int = 0,
    goodstypecode: str = "WPX",
    consigneetel: str = "",
    note: str = "",
) -> dict[str, Any]:
    """Create a new logistics order (运单) and submit it to forecast status.

    Args:
        channelid: Shipping channel code, e.g. "FEDEX-IP", "DHL-EXPRESS". Use query_channels to list available channels.
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
        return _service().create_order({
            "channelid": channelid,
            "customernumber1": customernumber1,
            "countrycode": countrycode,
            "consigneename": consigneename,
            "consigneeaddress1": consigneeaddress1,
            "consigneecity": consigneecity,
            "consigneezipcode": consigneezipcode,
            "consigneeprovince": consigneeprovince,
            "forecastweight": forecastweight,
            "number": number,
            "isbattery": isbattery,
            "goodstypecode": goodstypecode,
            "consigneetel": consigneetel,
            "note": note,
            "items": [
                {
                    "cnname": goods_cnname,
                    "weight": goods_weight_kg,
                    "quantity": goods_quantity,
                }
            ],
        })
    except Exception as exc:
        return LogisticsService.format_error(exc)


# ---------------------------------------------------------------------------
# 2. 查询运单 (Query Orders)
# ---------------------------------------------------------------------------

def query_orders(
    begcreatedate: str,
    endcreatedate: str,
    page: int = 1,
    limit: int = 10,
) -> dict[str, Any]:
    """Query orders by creation date range with pagination (分页查询运单).

    Args:
        begcreatedate: Start date in format "YYYY-MM-DD HH:MM:SS", e.g. "2026-04-01 00:00:00".
        endcreatedate: End date in format "YYYY-MM-DD HH:MM:SS", e.g. "2026-04-05 23:59:59".
        page: Page number starting from 1.
        limit: Number of orders per page (max 100).
    """
    try:
        return _service().query_orders({
            "begcreatedate": begcreatedate,
            "endcreatedate": endcreatedate,
            "page": page,
            "limit": limit,
        })
    except Exception as exc:
        return LogisticsService.format_error(exc)


# ---------------------------------------------------------------------------
# 3. 查询轨迹 (Track Shipment)
# ---------------------------------------------------------------------------

def track_shipment(
    number: str,
    number_type: str = "waybillnumber",
) -> dict[str, Any]:
    """Track a shipment by its number. Returns tracking events / trajectory (查询轨迹).

    Args:
        number: The tracking number to look up.
        number_type: Type of number — one of "waybillnumber" (运单号), "systemnumber" (系统单号), or "customernumber" (客户参考号).
    """
    try:
        return _service().track_shipment({number_type: [number]})
    except Exception as exc:
        return LogisticsService.format_error(exc)


# ---------------------------------------------------------------------------
# 4. 运费试算 (Estimate Shipping Cost for a specific channel)
# ---------------------------------------------------------------------------

def estimate_shipping_cost(
    channelid: str,
    countrycode: str,
    forecastweight: float,
    number: int = 1,
    isbattery: int = 0,
    goodstypecode: str = "WPX",
) -> dict[str, Any]:
    """Estimate shipping cost for a specific channel (运费试算).

    Args:
        channelid: Channel code, e.g. "FEDEX-IP". Use query_channels to list available channels.
        countrycode: Destination country ISO code, e.g. "US".
        forecastweight: Total weight in KG.
        number: Number of packages.
        isbattery: Whether contains battery (0=no, 1=yes).
        goodstypecode: Goods type (WPX/DOC/PAK).
    """
    try:
        return _service().estimate_channel_price({
            "channelid": channelid,
            "countrycode": countrycode,
            "forecastweight": forecastweight,
            "number": number,
            "isbattery": isbattery,
            "goodstypecode": goodstypecode,
        })
    except Exception as exc:
        return LogisticsService.format_error(exc)


# ---------------------------------------------------------------------------
# 5. 查询报价 (Compare prices across channels)
# ---------------------------------------------------------------------------

def query_price(
    dest: str,
    weight: float,
    piece: int = 1,
    goodstype: str = "WPX",
    desttype: str = "country",
    channelid: str = "",
) -> dict[str, Any]:
    """Compare shipping prices across all available channels for a destination (查询报价).

    Args:
        dest: Destination code, e.g. "US", "GB", "JP". Use query_destinations to find valid codes.
        weight: Total weight in KG.
        piece: Total number of packages.
        goodstype: Goods type code (WPX=包裹, DOC=文件, PAK=PAK袋).
        desttype: Destination type — "country", "port", or "airport".
        channelid: Optional channel code to filter results to a single channel.
    """
    try:
        return _service().query_price({
            "dest": dest,
            "weight": weight,
            "piece": piece,
            "goodstype": goodstype,
            "desttype": desttype,
            "channelid": channelid,
        })
    except Exception as exc:
        return LogisticsService.format_error(exc)


# ---------------------------------------------------------------------------
# 6. 查询渠道 (List available channels)
# ---------------------------------------------------------------------------

def query_channels() -> dict[str, Any]:
    """List all available shipping channels (查询渠道).

    Returns channel codes, names, and types. Use the channelid in other tools
    like create_order or estimate_shipping_cost.
    """
    try:
        return _service().query_channels()
    except Exception as exc:
        return LogisticsService.format_error(exc)


# ---------------------------------------------------------------------------
# 7. 查询目的地 (Search destinations)
# ---------------------------------------------------------------------------

def query_destinations(
    dest: str = "",
    desttype: str = "country",
) -> dict[str, Any]:
    """Search supported destinations — countries, ports, or airports (查询目的地).

    Args:
        dest: Keyword to search, e.g. "US" or "美国". Leave empty to list all.
        desttype: Type — "country", "port", or "airport".
    """
    try:
        return _service().query_destinations({
            "dest": dest,
            "desttype": desttype,
        })
    except Exception as exc:
        return LogisticsService.format_error(exc)


# ---------------------------------------------------------------------------
# 8. 查询运单费用 (Get order fees)
# ---------------------------------------------------------------------------

def get_order_fees(
    waybillnumber: str,
) -> dict[str, Any]:
    """Get the fee breakdown for an order by its waybill number (获取运单费用).

    Args:
        waybillnumber: The waybill number (运单号) to query fees for.
    """
    try:
        return _service().get_order_fees({
            "waybillnumber": [waybillnumber],
        })
    except Exception as exc:
        return LogisticsService.format_error(exc)


# ---------------------------------------------------------------------------
# 9. 删除运单 (Delete order)
# ---------------------------------------------------------------------------

def delete_order(
    number: str,
    number_type: str = "customernumber",
) -> dict[str, Any]:
    """Delete an unshipped order. Only orders in draft or forecast status can be deleted (删除运单).

    Args:
        number: The order number to delete.
        number_type: Type of number — "customernumber" (客户参考号), "waybillnumber" (运单号), or "systemnumber" (系统单号).
    """
    try:
        return _service().delete_order({number_type: number})
    except Exception as exc:
        return LogisticsService.format_error(exc)
