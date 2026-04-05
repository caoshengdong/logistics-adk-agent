from __future__ import annotations

import json

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

if __name__ == "__main__":
    demos = {
        "1_query_channels": query_channels(),
        "2_query_destinations": query_destinations(dest="US"),
        "3_query_price": query_price(dest="US", weight=10.0),
        "4_estimate_shipping_cost": estimate_shipping_cost(
            channelid="FEDEX-IP", countrycode="US", forecastweight=10.0,
        ),
        "5_create_order": create_order(
            channelid="DHL-EXPRESS",
            customernumber1="TEST-CLI-001",
            countrycode="GB",
            consigneename="Test User",
            consigneeaddress1="123 Test St",
            consigneecity="London",
            consigneezipcode="SW1A 1AA",
            consigneeprovince="England",
            forecastweight=5.0,
            goods_cnname="测试商品",
            goods_weight_kg=2.5,
            goods_quantity=2,
        ),
        "6_query_orders": query_orders(
            begcreatedate="2026-01-01 00:00:00",
            endcreatedate="2026-12-31 23:59:59",
        ),
        "7_track_shipment": track_shipment(
            number="T6W20260401002", number_type="waybillnumber",
        ),
        "8_get_order_fees": get_order_fees(waybillnumber="T6W20260401003"),
        "9_delete_order": delete_order(
            number="CUST-20260401-001", number_type="customernumber",
        ),
    }
    print(json.dumps(demos, indent=2, ensure_ascii=False))
