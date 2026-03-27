from __future__ import annotations

import json

from logistics_agent.tools.logistics_tools import (
    create_freight_shipment,
    get_order_shipping_status,
    get_shipment_status,
    quote_freight_rate,
)


if __name__ == "__main__":
    demos = {
        "track_order_12345": get_order_shipping_status("12345"),
        "quote_shenzhen_to_los_angeles": quote_freight_rate(
            origin="Shenzhen, CN",
            destination="Los Angeles, US",
            weight_kg=42.0,
            mode="air",
        ),
        "create_shipment": create_freight_shipment(
            origin="Shenzhen, CN",
            destination="Los Angeles, US",
            weight_kg=42.0,
            goods_description="Consumer electronics",
            mode="air",
            order_id="98765",
            customer_reference="PO-2026-0001",
        ),
        "track_seeded_shipment": get_shipment_status("SHP-10001"),
    }
    print(json.dumps(demos, indent=2, ensure_ascii=False))
