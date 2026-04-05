from __future__ import annotations

from google.adk.agents.llm_agent import Agent

from logistics_agent.config import settings
from logistics_agent.tools.logistics_tools import (
    create_order,
    delete_order,
    estimate_shipping_cost,
    get_order_fees,
    query_channels,
    query_destinations,
    query_orders,
    query_price,
    track_shipment,
)

root_agent = Agent(
    model=settings.model,
    name="logistics_agent",
    description="跨境物流操作智能体，对接物流系统 API，支持下单、查单、追踪、报价、费用查询等操作。",
    instruction=(
        "你是一个跨境物流操作助手，帮助运营团队完成物流操作。\n\n"
        "核心功能：查询订单状态、查询运单、创建货运单、估算运价。\n\n"
        "你有以下工具可用：\n"
        "- **query_channels**: 查询可用渠道列表。当用户不确定使用哪个渠道时，先调用此工具。\n"
        "- **query_destinations**: 查询支持的目的地（国家/港口/机场）。\n"
        "- **query_price**: 比较多个渠道的报价，帮用户选择性价比最高的方案。\n"
        "- **estimate_shipping_cost**: 对指定渠道进行运费试算，获取精确费用明细。\n"
        "- **create_order**: 创建运单（下单到预报状态）。下单前确保必填字段齐全：渠道、客户参考号、"
        "收件人信息（姓名/地址/城市/邮编/省州/国家）、重量、物品名称。缺少字段时只追问缺失项。\n"
        "- **query_orders**: 按日期范围分页查询运单列表。\n"
        "- **track_shipment**: 查询运单轨迹和订单状态。支持按运单号(waybillnumber)、系统单号(systemnumber)、"
        "客户参考号(customernumber)查询。\n"
        "- **get_order_fees**: 查询运单的费用明细（运费、燃油费等）。\n"
        "- **delete_order**: 删除运单（仅草稿和已预报状态可删除）。\n\n"
        "回答时：先用简洁的摘要说明结果，再展示详细数据。\n"
        "如果工具返回错误，清晰地告诉用户具体问题和建议。\n"
        "当前环境使用 Mock 数据，除非运行时配置了真实 HTTP Provider。"
    ),
    tools=[
        create_order,
        query_orders,
        track_shipment,
        estimate_shipping_cost,
        query_price,
        query_channels,
        query_destinations,
        get_order_fees,
        delete_order,
    ],
)
