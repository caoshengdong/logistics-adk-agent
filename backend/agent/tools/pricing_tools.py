"""Pricing & channel discovery tools: price comparison, cost estimation, channels, destinations."""

from __future__ import annotations

from typing import Any

from google.adk.tools import ToolContext

from agent.services.logistics_service import LogisticsService
from agent.tools._common import resolve_service


def _save_state(tool_context: ToolContext | None, key: str, value: Any) -> None:
    """Write a value into ADK session state (for cross-agent context sharing)."""
    if tool_context is not None:
        tool_context.state[key] = value


def estimate_shipping_cost(
    channelid: str,
    countrycode: str,
    forecastweight: float,
    number: int = 1,
    isbattery: int = 0,
    goodstypecode: str = "WPX",
    tool_context: ToolContext | None = None,
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
        result = resolve_service(tool_context).estimate_channel_price({
            "channelid": channelid,
            "countrycode": countrycode,
            "forecastweight": forecastweight,
            "number": number,
            "isbattery": isbattery,
            "goodstypecode": goodstypecode,
        })
        # ── Compress into state ──
        if result.get("status") == "success" and result.get("data"):
            item = result["data"][0]
            _save_state(tool_context, "last_estimate_channel", channelid)
            _save_state(tool_context, "last_estimate_total",
                        f"{item.get('amount', '?')} RMB")
        return result
    except Exception as exc:
        return LogisticsService.format_error(exc)


def query_price(
    dest: str,
    weight: float,
    piece: int = 1,
    goodstype: str = "WPX",
    desttype: str = "country",
    channelid: str = "",
    tool_context: ToolContext | None = None,
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
        result = resolve_service(tool_context).query_price({
            "dest": dest,
            "weight": weight,
            "piece": piece,
            "goodstype": goodstype,
            "desttype": desttype,
            "channelid": channelid,
        })
        # ── Compress into state: compact quote summary ──
        if result.get("status") == "success" and result.get("data"):
            channels = result["data"]
            # Sort by price, store top-3 cheapest as compact string
            sorted_ch = sorted(channels, key=lambda c: c.get("totalCost", 9999))
            summary_parts = [
                f"{c['channel']['channelid']}={c['totalCost']}RMB"
                for c in sorted_ch[:3]
                if "channel" in c
            ]
            _save_state(tool_context, "last_quote_summary",
                        f"{dest}/{weight}kg top3: " + ", ".join(summary_parts))
            if sorted_ch:
                cheapest = sorted_ch[0]
                _save_state(tool_context, "last_cheapest_channel",
                            cheapest.get("channel", {}).get("channelid", ""))
            # New comparison supersedes any previous single-channel estimate
            _save_state(tool_context, "last_estimate_channel", "")
            _save_state(tool_context, "last_estimate_total", "")
        return result
    except Exception as exc:
        return LogisticsService.format_error(exc)


def query_channels(
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """List all available shipping channels (查询渠道).

    Returns channel codes, names, and types. Use the channelid in other tools
    like create_order or estimate_shipping_cost.
    """
    try:
        return resolve_service(tool_context).query_channels()
    except Exception as exc:
        return LogisticsService.format_error(exc)


def query_destinations(
    dest: str = "",
    desttype: str = "country",
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Search supported destinations — countries, ports, or airports (查询目的地).

    Args:
        dest: Keyword to search, e.g. "US" or "美国". Leave empty to list all.
        desttype: Type — "country", "port", or "airport".
    """
    try:
        return resolve_service(tool_context).query_destinations({
            "dest": dest,
            "desttype": desttype,
        })
    except Exception as exc:
        return LogisticsService.format_error(exc)


def generate_quotation_pdf(
    dest: str,
    weight: float,
    piece: int = 1,
    goodstype: str = "WPX",
    channelid: str = "",
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Generate a downloadable PDF quotation comparing shipping prices (生成报价单PDF).

    This queries prices across channels and produces a professional PDF document
    that the user can download. The PDF is saved as an artifact.

    Args:
        dest: Destination country code, e.g. "US", "GB", "JP".
        weight: Total weight in KG.
        piece: Number of packages.
        goodstype: Goods type code (WPX/DOC/PAK).
        channelid: Optional channel code to filter results.
    """
    try:
        service = resolve_service(tool_context)
        pdf_bytes, filename, price_result = service.generate_quotation_pdf({
            "dest": dest,
            "weight": weight,
            "piece": piece,
            "goodstype": goodstype,
            "channelid": channelid,
        })

        # Save PDF directly to PostgreSQL — bypasses ADK's artifact Part flow
        # to avoid the copy.deepcopy / coroutine pickle error.
        if tool_context is not None:
            session_id = tool_context.state.get("_session_id", "")
            user_id = tool_context.state.get("_user_id", "")

            if session_id and user_id:
                from app.chat.db_artifact_service import save_artifact_to_db

                artifact_id, version = save_artifact_to_db(
                    session_id=session_id,
                    user_id=user_id,
                    filename=filename,
                    data=pdf_bytes,
                    content_type="application/pdf",
                )

                channel_count = len(price_result.get("data", []))
                return {
                    "status": "success",
                    "message": (
                        f"报价单 PDF 已生成：{filename}，"
                        f"包含 {channel_count} 个渠道的报价对比。"
                        "用户可以点击下载按钮获取文件。"
                    ),
                    "artifact_id": artifact_id,
                    "filename": filename,
                    "content_type": "application/pdf",
                    "size": len(pdf_bytes),
                    "artifact_version": version,
                    "channel_count": channel_count,
                }

        return {"status": "error", "message": "无法保存文件（缺少工具上下文）"}
    except Exception as exc:
        return LogisticsService.format_error(exc)


