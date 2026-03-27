from __future__ import annotations

from google.adk.agents.llm_agent import Agent

from logistics_agent.config import settings
from logistics_agent.tools.logistics_tools import (
    create_freight_shipment,
    get_order_shipping_status,
    get_shipment_status,
    quote_freight_rate,
)

root_agent = Agent(
    model=settings.model,
    name="logistics_agent",
    description="Logistics operations agent for shipment tracking, shipment creation, and freight quote workflows.",
    instruction=(
        "You are a logistics operations copilot for an internal operations team. "
        "Use tools for all shipment lookups, shipment creation, and freight quote requests. "
        "Use get_order_shipping_status when the user gives an order number. "
        "Use get_shipment_status when the user gives a shipment id. "
        "Before creating a shipment, ensure origin, destination, weight, and goods description are present. "
        "If any required field is missing, ask only for the missing field. "
        "When a tool returns an error, surface the exact issue clearly. "
        "When returning tracking results, summarize current status, ETA, route, and latest milestone first, then provide details. "
        "Treat all provider results as mock data unless the runtime is configured to use a real HTTP provider."
    ),
    tools=[
        get_order_shipping_status,
        get_shipment_status,
        create_freight_shipment,
        quote_freight_rate,
    ],
)
