"""Mock provider producing realistic logistics-system-shaped data for local development."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from agent.models.domain import (
    ChannelPriceRequest,
    CreateOrderRequest,
    DeleteOrderRequest,
    DestQueryParams,
    OrderFeesRequest,
    OrderNotFoundError,
    PriceQueryRequest,
    QueryOrdersRequest,
    T6Channel,
    T6ChannelPriceDetail,
    T6ChannelPriceResult,
    T6Destination,
    T6FeeItem,
    T6Order,
    T6OrderFees,
    T6PriceChannel,
    T6PriceResult,
    T6TrackEvent,
    T6TrackResult,
    TrackRequest,
    now_str,
    now_utc,
)
from agent.providers.base import LogisticsProvider

# ---------------------------------------------------------------------------
# Seed data helpers
# ---------------------------------------------------------------------------

_MOCK_CHANNELS: list[T6Channel] = [
    T6Channel(channelid="FEDEX-IP", channeltype="快递", channelname="联邦快递",
              channelnamecn="联邦国际优先", channelnameen="FedEx International Priority"),
    T6Channel(channelid="DHL-EXPRESS", channeltype="快递", channelname="DHL快递",
              channelnamecn="DHL国际快递", channelnameen="DHL Express Worldwide"),
    T6Channel(channelid="UPS-EXP", channeltype="快递", channelname="UPS快递",
              channelnamecn="UPS全球速运", channelnameen="UPS Worldwide Express"),
    T6Channel(channelid="YANWEN-STD", channeltype="专线", channelname="燕文标准",
              channelnamecn="燕文标准专线", channelnameen="Yanwen Standard"),
    T6Channel(channelid="MS-KQ", channeltype="专线", channelname="美森快船",
              channelnamecn="美森快船专线", channelnameen="Mason Clippers"),
    T6Channel(channelid="CN-EMS", channeltype="邮政", channelname="中国邮政EMS",
              channelnamecn="中国邮政国际EMS", channelnameen="China Post EMS"),
    T6Channel(channelid="SF-INTL", channeltype="快递", channelname="顺丰国际",
              channelnamecn="顺丰国际快递", channelnameen="SF International Express"),
]

_MOCK_DESTINATIONS: list[T6Destination] = [
    T6Destination(destName="美国", destCode="US"),
    T6Destination(destName="英国", destCode="GB"),
    T6Destination(destName="德国", destCode="DE"),
    T6Destination(destName="法国", destCode="FR"),
    T6Destination(destName="日本", destCode="JP"),
    T6Destination(destName="澳大利亚", destCode="AU"),
    T6Destination(destName="加拿大", destCode="CA"),
    T6Destination(destName="俄罗斯", destCode="RU"),
    T6Destination(destName="巴西", destCode="BR"),
    T6Destination(destName="新加坡", destCode="SG"),
]


def _seed_orders() -> list[T6Order]:
    """Generate a handful of seed orders for demo/testing."""
    base_time = now_utc()
    return [
        T6Order(
            pkid=10001,
            systemnumber="SYS20260401001",
            customernumber1="CUST-20260401-001",
            waybillnumber="T6W20260401001",
            tracknumber="1Z64104F6795715591",
            channelid="FEDEX-IP",
            channelname="联邦国际优先",
            countrycode="US",
            countryname="美国",
            number=2,
            status="Predicted",
            statusname="已预报",
            forecastweight=15.5,
            inrweight=0.0,
            consigneename="John Smith",
            consigneecity="Los Angeles",
            consigneeprovince="CA",
            consigneezipcode="90001",
            createdate=(base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
            editdate=(base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            note="电子产品，注意防震",
        ),
        T6Order(
            pkid=10002,
            systemnumber="SYS20260401002",
            customernumber1="CUST-20260401-002",
            waybillnumber="T6W20260401002",
            tracknumber="1Z5VT6220478322140",
            channelid="DHL-EXPRESS",
            channelname="DHL国际快递",
            countrycode="GB",
            countryname="英国",
            number=1,
            status="Shipped",
            statusname="已发货",
            forecastweight=3.2,
            inrweight=3.3,
            consigneename="Emma Watson",
            consigneecity="London",
            consigneeprovince="England",
            consigneezipcode="SW1A 1AA",
            createdate=(base_time - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
            editdate=(base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            note="服装样品",
        ),
        T6Order(
            pkid=10003,
            systemnumber="SYS20260401003",
            customernumber1="CUST-20260401-003",
            waybillnumber="T6W20260401003",
            tracknumber="",
            channelid="MS-KQ",
            channelname="美森快船专线",
            countrycode="US",
            countryname="美国",
            number=5,
            status="Sign",
            statusname="已签收",
            forecastweight=120.0,
            inrweight=118.5,
            consigneename="Alice Johnson",
            consigneecity="New York",
            consigneeprovince="NY",
            consigneezipcode="10001",
            createdate=(base_time - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
            editdate=(base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            note="家居用品批量发货",
        ),
        T6Order(
            pkid=10004,
            systemnumber="SYS20260401004",
            customernumber1="CUST-20260401-004",
            waybillnumber="T6W20260401004",
            tracknumber="JD0042726839",
            channelid="SF-INTL",
            channelname="顺丰国际快递",
            countrycode="JP",
            countryname="日本",
            number=1,
            status="InTransit",
            statusname="运输中",
            forecastweight=2.1,
            inrweight=2.0,
            consigneename="田中太郎",
            consigneecity="東京",
            consigneeprovince="東京都",
            consigneezipcode="100-0001",
            createdate=(base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            editdate=(base_time - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
            note="化妆品小样",
        ),
    ]


def _seed_tracks() -> dict[str, T6TrackResult]:
    """Generate track results keyed by waybillnumber / systemnumber / customernumber."""
    base_time = now_utc()
    t1 = T6TrackResult(
        searchNumber="T6W20260401001",
        systemnumber="SYS20260401001",
        waybillnumber="T6W20260401001",
        tracknumber="1Z64104F6795715591",
        countrycode="US",
        orderstatus="Predicted",
        orderstatusName="已预报",
        trackItems=[
            T6TrackEvent(
                trackdate=(base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
                trackdate_utc8=(base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
                location="深圳, CN",
                info="运单已创建，等待揽收",
                responsecode="OT001",
            ),
            T6TrackEvent(
                trackdate=(
                    base_time - timedelta(days=2, hours=18)
                ).strftime("%Y-%m-%d %H:%M:%S"),
                trackdate_utc8=(
                    base_time - timedelta(days=2, hours=18)
                ).strftime("%Y-%m-%d %H:%M:%S"),
                location="深圳, CN",
                info="包裹已揽收",
                responsecode="OT001",
            ),
        ],
    )
    t2 = T6TrackResult(
        searchNumber="T6W20260401002",
        systemnumber="SYS20260401002",
        waybillnumber="T6W20260401002",
        tracknumber="1Z5VT6220478322140",
        countrycode="GB",
        orderstatus="Shipped",
        orderstatusName="已发货",
        trackItems=[
            T6TrackEvent(
                trackdate=(base_time - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
                trackdate_utc8=(base_time - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
                location="深圳, CN",
                info="运单已创建",
                responsecode="OT001",
            ),
            T6TrackEvent(
                trackdate=(base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
                trackdate_utc8=(base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
                location="深圳, CN",
                info="已离开深圳分拨中心",
                responsecode="OT001",
            ),
            T6TrackEvent(
                trackdate=(base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
                trackdate_utc8=(base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
                location="香港, CN",
                info="航班已起飞",
                responsecode="OT001",
            ),
            T6TrackEvent(
                trackdate=(base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                trackdate_utc8=(base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                location="London, GB",
                info="到达目的国，等待清关",
                responsecode="OT001",
            ),
        ],
    )
    t3 = T6TrackResult(
        searchNumber="T6W20260401003",
        systemnumber="SYS20260401003",
        waybillnumber="T6W20260401003",
        countrycode="US",
        orderstatus="Sign",
        orderstatusName="已签收",
        trackItems=[
            T6TrackEvent(
                trackdate=(base_time - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
                trackdate_utc8=(base_time - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
                location="深圳, CN",
                info="运单已创建",
                responsecode="OT001",
            ),
            T6TrackEvent(
                trackdate=(base_time - timedelta(days=25)).strftime("%Y-%m-%d %H:%M:%S"),
                trackdate_utc8=(base_time - timedelta(days=25)).strftime("%Y-%m-%d %H:%M:%S"),
                location="盐田港, CN",
                info="已装船出港",
                responsecode="OT001",
            ),
            T6TrackEvent(
                trackdate=(base_time - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
                trackdate_utc8=(base_time - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
                location="Los Angeles, US",
                info="到达港口，开始清关",
                responsecode="OT001",
            ),
            T6TrackEvent(
                trackdate=(base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                trackdate_utc8=(base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                location="New York, US",
                info="已递送，签收人: Alice Johnson",
                responsecode="OT001",
            ),
        ],
    )
    t4 = T6TrackResult(
        searchNumber="T6W20260401004",
        systemnumber="SYS20260401004",
        waybillnumber="T6W20260401004",
        tracknumber="JD0042726839",
        countrycode="JP",
        orderstatus="InTransit",
        orderstatusName="运输中",
        trackItems=[
            T6TrackEvent(
                trackdate=(base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                trackdate_utc8=(base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                location="深圳, CN",
                info="运单已创建，已揽收",
                responsecode="OT001",
            ),
            T6TrackEvent(
                trackdate=(base_time - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"),
                trackdate_utc8=(base_time - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"),
                location="上海浦东机场, CN",
                info="航班已起飞，前往东京",
                responsecode="OT001",
            ),
        ],
    )
    # Build lookup maps: waybillnumber -> track, systemnumber -> track, customernumber -> track
    results: dict[str, T6TrackResult] = {}
    for t in [t1, t2, t3, t4]:
        results[t.waybillnumber] = t
        results[t.systemnumber] = t
    # Also index by customernumber
    cust_map = {
        "CUST-20260401-001": t1,
        "CUST-20260401-002": t2,
        "CUST-20260401-003": t3,
        "CUST-20260401-004": t4,
    }
    results.update(cust_map)
    return results


# ---------------------------------------------------------------------------
# Mock Provider
# ---------------------------------------------------------------------------

@dataclass
class MockLogisticsProvider(LogisticsProvider):
    orders: dict[str, T6Order] = field(default_factory=dict)
    tracks: dict[str, T6TrackResult] = field(default_factory=dict)
    _next_pkid: int = field(default=20000)

    def __post_init__(self) -> None:
        if not self.orders:
            self._seed_data()

    def _seed_data(self) -> None:
        for order in _seed_orders():
            self.orders[order.waybillnumber] = order
            self.orders[order.systemnumber] = order
            self.orders[order.customernumber1] = order
        self.tracks = _seed_tracks()

    # --- create_order ---
    def create_order(self, request: CreateOrderRequest) -> dict[str, Any]:
        self._next_pkid += 1
        sys_number = f"SYS{now_utc().strftime('%Y%m%d')}{self._next_pkid:03d}"
        waybill = f"T6W{now_utc().strftime('%Y%m%d')}{self._next_pkid:03d}"

        order = T6Order(
            pkid=self._next_pkid,
            systemnumber=sys_number,
            customernumber1=request.customernumber1,
            customernumber2=request.customernumber2,
            waybillnumber=waybill,
            channelid=request.channelid,
            channelname=request.channelid,
            countrycode=request.countrycode,
            number=request.number,
            status="Predicted",
            statusname="已预报",
            forecastweight=request.forecastweight,
            consigneename=request.consigneename,
            consigneecity=request.consigneecity,
            consigneeprovince=request.consigneeprovince,
            consigneezipcode=request.consigneezipcode,
            createdate=now_str(),
            editdate=now_str(),
            note=request.note,
        )
        self.orders[waybill] = order
        self.orders[sys_number] = order
        self.orders[request.customernumber1] = order

        return {
            "code": 0,
            "msg": "调用成功",
            "data": [
                {
                    "code": 0,
                    "msg": "下单成功",
                    "customernumber": request.customernumber1,
                    "systemnumber": sys_number,
                    "waybillnumber": waybill,
                }
            ],
        }

    # --- query_orders ---
    def query_orders(self, request: QueryOrdersRequest) -> dict[str, Any]:
        # Deduplicate orders (same order indexed by multiple keys)
        unique: dict[int, T6Order] = {}
        for o in self.orders.values():
            if o.pkid not in unique:
                # Lenient date filtering for mock: include order if its
                # createdate falls within the requested range.
                in_range = request.begcreatedate <= o.createdate <= request.endcreatedate
                if in_range:
                    unique[o.pkid] = o

        # If strict filtering returned nothing, fall back to returning all
        # orders.  This makes the demo more resilient to imprecise date
        # ranges produced by the LLM.
        if not unique:
            seen: set[int] = set()
            for o in self.orders.values():
                if o.pkid not in seen:
                    unique[o.pkid] = o
                    seen.add(o.pkid)

        all_orders = sorted(unique.values(), key=lambda x: x.createdate, reverse=True)
        total = len(all_orders)
        start = (request.page - 1) * request.limit
        page_orders = all_orders[start: start + request.limit]

        return {
            "status": "success",
            "code": 0,
            "count": total,
            "data": [o.model_dump(mode="json") for o in page_orders],
        }

    # --- track_shipment ---
    def track_shipment(self, request: TrackRequest) -> dict[str, Any]:
        numbers: list[str] = []
        if request.waybillnumber:
            numbers = request.waybillnumber
        elif request.systemnumber:
            numbers = request.systemnumber
        elif request.customernumber:
            numbers = request.customernumber

        results: list[dict[str, Any]] = []
        for num in numbers:
            track = self.tracks.get(num)
            if track:
                results.append(track.model_dump(mode="json"))
            else:
                results.append({"searchNumber": num, "errormsg": "无效的单号"})

        return {"status": "success", "code": 0, "msg": "success", "data": results}

    # --- estimate_channel_price ---
    def estimate_channel_price(self, request: ChannelPriceRequest) -> dict[str, Any]:
        # Simple mock pricing: base rate by channel type
        channel_rates = {
            "FEDEX-IP": 45.0,
            "DHL-EXPRESS": 42.0,
            "UPS-EXP": 40.0,
            "SF-INTL": 35.0,
            "YANWEN-STD": 18.0,
            "MS-KQ": 12.0,
            "CN-EMS": 25.0,
        }
        base_rate = channel_rates.get(request.channelid, 30.0)
        freight = round(base_rate * request.forecastweight, 2)
        fuel = round(freight * 0.125, 2)
        total = round(freight + fuel, 2)

        result = T6ChannelPriceResult(
            code=0,
            msg="成功",
            amount=total,
            details=[
                T6ChannelPriceDetail(amount=freight, code="RMB", name="人民币", type="运费"),
                T6ChannelPriceDetail(amount=fuel, code="RMB", name="人民币", type="燃油费"),
            ],
        )
        return {"code": 0, "msg": "调用成功", "data": [result.model_dump(mode="json")]}

    # --- query_price ---
    def query_price(self, request: PriceQueryRequest) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        for ch in _MOCK_CHANNELS:
            channel_rates = {
                "FEDEX-IP": 45.0, "DHL-EXPRESS": 42.0, "UPS-EXP": 40.0,
                "SF-INTL": 35.0, "YANWEN-STD": 18.0, "MS-KQ": 12.0, "CN-EMS": 25.0,
            }
            aging_map = {
                "FEDEX-IP": "3-5天", "DHL-EXPRESS": "3-5天", "UPS-EXP": "3-5天",
                "SF-INTL": "4-6天", "YANWEN-STD": "7-15天", "MS-KQ": "20-30天", "CN-EMS": "7-12天",
            }
            if request.channelid and ch.channelid != request.channelid:
                continue

            base_rate = channel_rates.get(ch.channelid, 30.0)
            tran_cost = round(base_rate * request.weight, 2)
            fuel_rate = 0.125
            fuel_cost = round(tran_cost * fuel_rate, 2)
            total = round(tran_cost + fuel_cost, 2)

            price_result = T6PriceResult(
                channel=T6PriceChannel(
                    channelid=ch.channelid,
                    channelname=ch.channelname,
                    channelnamecn=ch.channelnamecn,
                    channelnameen=ch.channelnameen,
                    aging=aging_map.get(ch.channelid, ""),
                ),
                totalCost=total,
                totalCostCcy="RMB",
                weight=request.weight,
                tranCost=tran_cost,
                fuelCost=fuel_cost,
                fuelCostRate=fuel_rate,
            )
            results.append(price_result.model_dump(mode="json"))

        return {"code": 0, "msg": "success", "data": results}

    # --- query_channels ---
    def query_channels(self) -> dict[str, Any]:
        return {
            "code": 0,
            "msg": "调用成功",
            "data": [ch.model_dump(mode="json") for ch in _MOCK_CHANNELS],
        }

    # --- query_destinations ---
    def query_destinations(self, params: DestQueryParams) -> dict[str, Any]:
        keyword = params.dest.upper()
        matches = [
            d for d in _MOCK_DESTINATIONS
            if not keyword or keyword in d.destCode.upper() or keyword in d.destName
        ]
        return {
            "code": 0,
            "msg": "success",
            "data": [d.model_dump(mode="json") for d in matches],
        }

    # --- get_order_fees ---
    def get_order_fees(self, request: OrderFeesRequest) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        for num in (request.waybillnumber or []):
            order = self.orders.get(num)
            if not order:
                results.append({"searchNumber": num, "errormsg": "无效的单号"})
                continue

            # Generate mock fees
            weight = order.inrweight or order.forecastweight
            freight = round(weight * 35.0, 2)
            fuel = round(freight * 0.125, 2)
            reg_fee = 5.0

            fees = T6OrderFees(
                searchNumber=num,
                inrweight=order.inrweight,
                inmweight=0.0,
                clientweight=weight,
                number=order.number,
                recsheetList=[
                    T6FeeItem(
                        sheetid=f"RS-{order.pkid}-01",
                        costtype="FREIGHT",
                        costtypeName="运费",
                        amount=freight,
                        currency="RMB",
                        currencyName="人民币",
                    ),
                    T6FeeItem(
                        sheetid=f"RS-{order.pkid}-02",
                        costtype="FUEL",
                        costtypeName="燃油费",
                        amount=fuel,
                        currency="RMB",
                        currencyName="人民币",
                    ),
                    T6FeeItem(
                        sheetid=f"RS-{order.pkid}-03",
                        costtype="REGISTER",
                        costtypeName="挂号费",
                        amount=reg_fee,
                        currency="RMB",
                        currencyName="人民币",
                    ),
                ],
            )
            results.append(fees.model_dump(mode="json"))

        return {"code": 0, "msg": "success", "data": results}

    # --- delete_order ---
    def delete_order(self, request: DeleteOrderRequest) -> dict[str, Any]:
        lookup_key = request.customernumber or request.waybillnumber or request.systemnumber
        if not lookup_key:
            return {"code": -1, "msg": "未提供单号"}

        order = self.orders.get(lookup_key)
        if not order:
            raise OrderNotFoundError(f"未找到单号: {lookup_key}")

        # Only allow deleting draft / predicted orders
        if order.status not in ("Draft", "Predicted"):
            return {
                "code": -1,
                "msg": (
                    f"运单状态为「{order.statusname}」，"
                    "无法删除，仅草稿和已预报状态可删除"
                ),
            }

        # Remove all index keys for this order
        keys_to_remove = [
            k for k, v in self.orders.items() if v.pkid == order.pkid
        ]
        for k in keys_to_remove:
            del self.orders[k]
        # Also remove tracks
        for k in list(self.tracks.keys()):
            t = self.tracks[k]
            if t.systemnumber == order.systemnumber:
                del self.tracks[k]

        return {"code": 0, "msg": "删除成功"}

    # --- generate_quotation_pdf ---
    def generate_quotation_pdf(self, price_data: dict[str, Any]) -> bytes:
        """Generate a professional quotation PDF from price query results."""
        from fpdf import FPDF

        items: list[dict[str, Any]] = price_data.get("data", [])
        query_params = price_data.get("query_params", {})
        dest = query_params.get("dest", "N/A")
        weight = query_params.get("weight", "N/A")
        piece = query_params.get("piece", 1)
        goodstype = query_params.get("goodstype", "WPX")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        # ── Header ─────────────────────────────────────────────────
        pdf.set_fill_color(30, 58, 138)  # indigo-900
        pdf.rect(0, 0, 210, 42, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_y(10)
        pdf.cell(0, 10, "Logistics AI", align="L", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(
            0, 7, "Shipping Quotation / Quotation Sheet",
            align="L", new_x="LMARGIN", new_y="NEXT",
        )

        # Date on the right side of the header
        pdf.set_xy(130, 12)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, f"Date: {now_utc().strftime('%Y-%m-%d')}", align="R")
        pdf.set_xy(130, 19)
        valid_date = (now_utc() + timedelta(days=7)).strftime("%Y-%m-%d")
        pdf.cell(0, 7, f"Valid Until: {valid_date}", align="R")

        pdf.ln(20)

        # ── Query Parameters ───────────────────────────────────────
        pdf.set_text_color(30, 58, 138)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Quotation Details", new_x="LMARGIN", new_y="NEXT")

        pdf.set_draw_color(30, 58, 138)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        pdf.set_text_color(60, 60, 60)
        pdf.set_font("Helvetica", "", 10)
        params_data = [
            ("Destination", str(dest)),
            ("Weight (KG)", str(weight)),
            ("Pieces", str(piece)),
            ("Goods Type", str(goodstype)),
        ]
        for label, value in params_data:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(45, 7, f"{label}:", new_x="END")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(6)

        # ── Price Comparison Table ─────────────────────────────────
        pdf.set_text_color(30, 58, 138)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Channel Price Comparison", new_x="LMARGIN", new_y="NEXT")

        pdf.set_draw_color(30, 58, 138)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

        # Table header
        col_widths = [45, 30, 32, 28, 28, 27]
        headers = ["Channel", "Transit", "Freight", "Fuel", "Total", "Currency"]

        pdf.set_fill_color(240, 244, 255)
        pdf.set_text_color(30, 58, 138)
        pdf.set_font("Helvetica", "B", 9)
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 8, h, border=1, align="C", fill=True, new_x="END")
        pdf.ln()

        # Table rows
        pdf.set_text_color(40, 40, 40)
        pdf.set_font("Helvetica", "", 9)

        # Sort by totalCost ascending
        sorted_items = sorted(items, key=lambda x: x.get("totalCost", 0))

        for idx, item in enumerate(sorted_items):
            ch = item.get("channel", {})
            channel_name = ch.get("channelnameen") or ch.get("channelid", "")
            # Convert aging to ASCII-safe format (e.g. "3-5天" → "3-5 days")
            aging_raw = ch.get("aging", "N/A")
            aging = aging_raw.replace("天", " days").replace("周", " weeks") if aging_raw else "N/A"
            tran_cost = f"{item.get('tranCost', 0):.2f}"
            fuel_cost = f"{item.get('fuelCost', 0):.2f}"
            total_cost = f"{item.get('totalCost', 0):.2f}"
            ccy = item.get("totalCostCcy", "RMB")

            # Alternate row color
            if idx % 2 == 0:
                pdf.set_fill_color(250, 250, 255)
            else:
                pdf.set_fill_color(255, 255, 255)

            # Highlight cheapest row
            if idx == 0:
                pdf.set_fill_color(220, 252, 231)  # green-100
                pdf.set_font("Helvetica", "B", 9)
            else:
                pdf.set_font("Helvetica", "", 9)

            row_data = [channel_name, aging, tran_cost, fuel_cost, total_cost, ccy]
            for j, val in enumerate(row_data):
                align = "L" if j == 0 else "C"
                pdf.cell(col_widths[j], 7, val, border=1, align=align, fill=True, new_x="END")
            pdf.ln()

        pdf.ln(8)

        # ── Footer Notes ───────────────────────────────────────────
        pdf.set_text_color(120, 120, 120)
        pdf.set_font("Helvetica", "I", 8)
        pdf.multi_cell(0, 5, (
            "Notes:\n"
            "1. Prices are estimates and may vary based on actual weight and dimensions.\n"
            "2. Fuel surcharge rates are subject to periodic adjustment.\n"
            "3. This quotation is valid for 7 days from the date of issue.\n"
            "4. Additional fees (remote area surcharge, customs duties, etc.) may apply."
        ))

        # Bottom bar
        pdf.set_y(-15)
        pdf.set_fill_color(30, 58, 138)
        pdf.rect(0, pdf.get_y(), 210, 15, "F")
        pdf.set_text_color(200, 210, 255)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 5, "Generated by Logistics AI Agent", align="C")

        return pdf.output()

