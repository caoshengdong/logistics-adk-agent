"""Multi-agent logistics system.

Architecture:
    root_agent (orchestrator)
    ├── order_agent      — Order management: create / query / delete shipments
    ├── tracking_agent   — Shipment tracking: trajectory lookup, fee breakdown
    └── pricing_agent    — Pricing & quotation: cost estimation,
                           multi-channel comparison, channel/destination lookup
"""

from __future__ import annotations

from google.adk.agents.llm_agent import Agent

from agent.config import settings
from agent.tools.order_tools import (
    create_order,
    delete_order,
    query_orders,
)
from agent.tools.pricing_tools import (
    estimate_shipping_cost,
    query_channels,
    query_destinations,
    query_price,
)
from agent.tools.tracking_tools import (
    get_order_fees,
    track_shipment,
)

# ---------------------------------------------------------------------------
# Sub-agent: Order Management
# ---------------------------------------------------------------------------

order_agent = Agent(
    model=settings.model,
    name="order_agent",
    description=(
        "Order management agent responsible for creating, "
        "querying, and deleting shipment orders."
    ),
    instruction=(
        "You are an Order Management Specialist handling "
        "the full lifecycle of shipment orders.\n\n"
        "Your tools:\n"
        "- **create_order**: Create a new shipment order "
        "(forecast status). Before placing an order, "
        "ensure all required fields are present: channel, "
        "customer reference number, "
        "recipient info (name / address / city / zip / "
        "state / country), weight, and goods name. "
        "If any field is missing, only ask for the "
        "missing ones.\n"
        "- **query_orders**: Query the order list by date "
        "range with pagination. **When the user asks for "
        "'recent orders' or 'my orders' without specifying "
        "dates, call this tool directly without providing "
        "begcreatedate/endcreatedate — it will default to "
        "the last 14 days. Do NOT ask the user for dates "
        "unless they explicitly want a custom range.**\n"
        "- **delete_order**: Delete an order (only draft "
        "and forecast statuses are deletable).\n\n"
        "If the user needs channel lookup or pricing, "
        "let them know you will hand off to the pricing "
        "specialist.\n"
        "When responding: provide a concise summary first, "
        "then show the detailed data."
    ),
    tools=[create_order, query_orders, delete_order],
)

# ---------------------------------------------------------------------------
# Sub-agent: Shipment Tracking
# ---------------------------------------------------------------------------

tracking_agent = Agent(
    model=settings.model,
    name="tracking_agent",
    description=(
        "Shipment tracking agent responsible for trajectory "
        "lookup, order status, and fee breakdown."
    ),
    instruction=(
        "You are a Shipment Tracking Specialist handling "
        "shipment visibility and cost inquiries.\n\n"
        "Your tools:\n"
        "- **track_shipment**: Query shipment trajectory "
        "and order status. Supports lookup by "
        "waybill number (waybillnumber), system number "
        "(systemnumber), or customer reference "
        "(customernumber).\n"
        "- **get_order_fees**: Query the fee breakdown "
        "for an order (freight, fuel surcharge, etc.).\n\n"
        "**IMPORTANT rules:**\n"
        "- Call each tool AT MOST ONCE per user request. "
        "NEVER retry the same tool with different parameters "
        "for the same shipment number.\n"
        "- If the result contains `errormsg` (e.g. '无效的单号'), "
        "the number is invalid. Report this to the user "
        "IMMEDIATELY and do NOT try again with a different "
        "number_type or any other workaround.\n"
        "- Do NOT guess or fabricate tracking numbers.\n\n"
        "When responding to tracking queries: present "
        "events in chronological order and highlight "
        "the current status.\n"
        "When responding to fee queries: list each fee "
        "item and the total amount."
    ),
    tools=[track_shipment, get_order_fees],
)

# ---------------------------------------------------------------------------
# Sub-agent: Pricing & Quotation
# ---------------------------------------------------------------------------

pricing_agent = Agent(
    model=settings.model,
    name="pricing_agent",
    description=(
        "Pricing and quotation agent responsible for "
        "shipping cost estimation, multi-channel price "
        "comparison, and channel/destination lookup."
    ),
    instruction=(
        "You are a Pricing & Quotation Specialist handling "
        "freight calculation and channel recommendations."
        "\n\n"
        "Your tools:\n"
        "- **query_channels**: List all available shipping "
        "channels. Call this first when the user is unsure "
        "which channel to use.\n"
        "- **query_destinations**: Search supported "
        "destinations (countries / ports / airports).\n"
        "- **query_price**: Compare quotes across multiple "
        "channels to help the user pick the most "
        "cost-effective option.\n"
        "- **estimate_shipping_cost**: Estimate the precise "
        "cost breakdown for a specific channel.\n\n"
        "When responding: sort channels from lowest to "
        "highest price, and include transit time and "
        "total cost.\n"
        "If the user wants to place an order, let them "
        "know you will hand off to the order specialist."
    ),
    tools=[estimate_shipping_cost, query_price, query_channels, query_destinations],
)

# ---------------------------------------------------------------------------
# Root Agent (orchestrator)
# ---------------------------------------------------------------------------

root_agent = Agent(
    model=settings.model,
    name="logistics_agent",
    description=(
        "Cross-border logistics orchestrator that coordinates "
        "specialized sub-agents for shipment operations."
    ),
    instruction=(
        "You are the chief dispatcher for a cross-border "
        "logistics assistant.\n\n"
        "## Current Customer Context\n"
        "- Customer code: {customer_code}\n"
        "- Customer name: {customer_name}\n"
        "(If the above fields are empty the session is in "
        "anonymous / mock mode.)\n\n"
        "Your job is to understand the user's intent and "
        "route requests to the right specialist.\n\n"
        "You have three specialist teams:\n"
        "1. **order_agent** (Order Specialist): handles "
        "creating, querying, and deleting shipment orders.\n"
        "2. **tracking_agent** (Tracking Specialist): "
        "handles shipment trajectory lookup and fee "
        "breakdown.\n"
        "3. **pricing_agent** (Pricing Specialist): handles "
        "cost estimation, multi-channel price comparison, "
        "channel lookup, and destination lookup.\n\n"
        "Routing rules:\n"
        "- Order list / create order / place order / "
        "delete order → route to order_agent\n"
        "- Track shipment / trajectory / order status / "
        "fee breakdown → route to tracking_agent\n"
        "- Quote / shipping cost / cheapest channel / "
        "available channels / destinations → "
        "route to pricing_agent\n\n"
        "**IMPORTANT: Error handling**\n"
        "- When a sub-agent reports that a number is invalid "
        "or not found, do NOT route to another sub-agent "
        "to retry the same lookup. Simply relay the error "
        "to the user and ask them to verify the number.\n"
        "- Each sub-agent should only be called ONCE per "
        "distinct task in the user's request.\n\n"
        "If a request spans multiple domains "
        "(e.g. 'get a quote then place an order'), "
        "dispatch to each specialist in sequence.\n"
        "Consolidate the sub-agent results and reply to "
        "the user with a concise summary.\n"
        "The current environment uses mock data unless a "
        "real HTTP provider is configured at runtime."
    ),
    sub_agents=[order_agent, tracking_agent, pricing_agent],
)
