"""Domain models aligned with the 跨境物流系统 API.

Field names intentionally mirror the remote API JSON schema so that the HTTP
provider can pass payloads through with minimal transformation, while the
Mock provider produces data in the same shape.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
UTC = timezone.utc


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def now_str() -> str:
    """Return current time as a standard datetime string."""
    return now_utc().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GoodsType(str, Enum):
    """货物类型 / Goods type codes."""
    WPX = "WPX"   # 包裹
    DOC = "DOC"   # 文件
    PAK = "PAK"   # PAK袋


class PackageType(str, Enum):
    """包裹类型."""
    GIFT = "G"       # 礼品
    SAMPLE = "C"     # 商品货样
    DOCUMENT = "D"   # 文件
    OTHER = "O"      # 其它


class DestType(str, Enum):
    """目的地类型."""
    COUNTRY = "country"
    PORT = "port"
    AIRPORT = "airport"


class OrderStatus(str, Enum):
    """运单状态编码."""
    DRAFT = "Draft"
    PREDICTED = "Predicted"    # 已预报
    RECEIVED = "Received"      # 已收货
    SHIPPED = "Shipped"        # 已发货
    IN_TRANSIT = "InTransit"   # 运输中
    CUSTOMS = "Customs"        # 清关中
    SIGN = "Sign"              # 已签收
    PROBLEM = "Problem"        # 问题件
    RETURNED = "Returned"      # 已退货


# ---------------------------------------------------------------------------
# Authorization (used internally by HTTP provider)
# ---------------------------------------------------------------------------

class T6Authorization(BaseModel):
    code: str = Field(..., min_length=1, description="客户编码")
    token: str = Field(..., min_length=1, description="API 授权码")


# ---------------------------------------------------------------------------
# Create Order request / response
# ---------------------------------------------------------------------------

class OrderItem(BaseModel):
    """物品信息 (items array inside order)."""
    cnname: str = Field(..., min_length=1, description="物品中文名")
    enname: str = Field("", description="物品英文名")
    weight: float = Field(..., gt=0, description="净重(KG)")
    quantity: int = Field(1, gt=0, description="数量")
    quantityunit: str = Field("PCS", description="数量单位")
    price: float = Field(0, ge=0, description="申报单价")
    declarecurrency: str = Field("USD", description="申报币别")
    hscode: str = Field("", description="海关编码")
    origin: str = Field("CN", description="产地")
    brand: str = Field("", description="品牌")
    skucode: str = Field("", description="SKU")


class OrderVolume(BaseModel):
    """材积信息."""
    customerchildnumber: str = Field("", description="客户子单号")
    prenum: int = Field(1, gt=0, description="件数")
    prelength: float = Field(0, ge=0, description="长(CM)")
    prewidth: float = Field(0, ge=0, description="宽(CM)")
    preheight: float = Field(0, ge=0, description="高(CM)")
    prerweight: float = Field(0, ge=0, description="单件重量(KG)")


class CreateOrderRequest(BaseModel):
    """Maps to POST /api/order/createForecast — simplified for agent use.

    Only the most essential fields are required; the rest have defaults.
    """
    channelid: str = Field(..., min_length=1, description="收货渠道编码")
    customernumber1: str = Field(..., min_length=1, description="客户参考号1")
    customernumber2: str = Field("", description="客户参考号2")
    number: int = Field(1, gt=0, description="总件数")
    forecastweight: float = Field(..., gt=0, description="预报总重量(KG)")
    isbattery: int = Field(0, description="是否带电(0否 1是)")
    ismagnet: int = Field(0, description="是否带磁(0否 1是)")
    isliquid: int = Field(0, description="是否液体(0否 1是)")
    ispowder: int = Field(0, description="是否粉末(0否 1是)")
    goodstypecode: str = Field("WPX", description="货物类型(WPX/DOC/PAK)")
    packagetypecode: str = Field("O", description="包裹类型(G/C/D/O)")

    # 收件人
    countrycode: str = Field(..., min_length=2, max_length=2, description="收件人国家编码")
    consigneename: str = Field(..., min_length=1, description="收件人名称")
    consigneecorpname: str = Field("", description="收件人公司")
    consigneeaddress1: str = Field(..., min_length=1, description="收件人地址1")
    consigneeaddress2: str = Field("", description="收件人地址2")
    consigneecity: str = Field(..., min_length=1, description="收件人城市")
    consigneezipcode: str = Field(..., min_length=1, description="收件人邮编")
    consigneeprovince: str = Field(..., min_length=1, description="收件人省州")
    consigneetel: str = Field("", description="收件人电话")
    consigneemobile: str = Field("", description="收件人手机")

    # 物品
    items: list[OrderItem] = Field(default_factory=list, description="物品信息")
    # 材积
    volumes: list[OrderVolume] = Field(default_factory=list, description="材积信息")

    note: str = Field("", description="运单备注")

    @field_validator("countrycode", mode="before")
    @classmethod
    def uppercase_country(cls, v: str) -> str:
        return v.strip().upper() if isinstance(v, str) else v


class CreateOrderResponse(BaseModel):
    """Single order result inside the batch response."""
    code: int
    msg: str
    customernumber: str = ""
    systemnumber: str = ""
    waybillnumber: str = ""


# ---------------------------------------------------------------------------
# Query Orders (pageOrders)
# ---------------------------------------------------------------------------

class QueryOrdersRequest(BaseModel):
    datatype: str = Field("1", description="日期类型(1制单时间 2最后修改时间)")
    begcreatedate: str = Field(..., description="起始日期 yyyy-MM-dd HH:mm:ss")
    endcreatedate: str = Field(..., description="截止日期 yyyy-MM-dd HH:mm:ss")
    page: int = Field(1, gt=0)
    limit: int = Field(10, gt=0, le=100)


class T6Order(BaseModel):
    """A single order returned from pageOrders."""
    pkid: int = 0
    systemnumber: str = ""
    customernumber1: str = ""
    customernumber2: str = ""
    waybillnumber: str = ""
    tracknumber: str = ""
    channelid: str = ""
    channelname: str = ""
    countrycode: str = ""
    countryname: str = ""
    number: int = 0
    status: str = ""
    statusname: str = ""
    forecastweight: float = 0.0
    inrweight: float = 0.0
    consigneename: str = ""
    consigneecity: str = ""
    consigneeprovince: str = ""
    consigneezipcode: str = ""
    createdate: str = ""
    editdate: str = ""
    note: str = ""


# ---------------------------------------------------------------------------
# Track
# ---------------------------------------------------------------------------

class TrackRequest(BaseModel):
    """Track request — exactly one of the three number lists should be set."""
    waybillnumber: Optional[list[str]] = None
    systemnumber: Optional[list[str]] = None
    customernumber: Optional[list[str]] = None

    @field_validator("waybillnumber", "systemnumber", "customernumber", mode="before")
    @classmethod
    def wrap_single_str(cls, v: Any) -> Any:
        """Allow passing a single string — auto-wrap into a list."""
        if isinstance(v, str):
            return [v]
        return v


class T6TrackEvent(BaseModel):
    trackdate: str = ""
    trackdate_utc8: str = ""
    location: str = ""
    info: str = ""
    responsecode: str = ""


class T6TrackResult(BaseModel):
    searchNumber: str = ""
    systemnumber: str = ""
    waybillnumber: str = ""
    tracknumber: str = ""
    countrycode: str = ""
    orderstatus: str = ""
    orderstatusName: str = ""
    trackItems: list[T6TrackEvent] = Field(default_factory=list)
    errormsg: str = ""


# ---------------------------------------------------------------------------
# Estimate Shipping Cost (searchChannelPrice)
# ---------------------------------------------------------------------------

class ChannelPriceRequest(BaseModel):
    channelid: str = Field(..., min_length=1, description="渠道编码")
    customernumber1: str = Field("QUOTE-TEMP", description="客户参考号(试算用)")
    number: int = Field(1, gt=0, description="总件数")
    forecastweight: float = Field(..., gt=0, description="预报总重量(KG)")
    isbattery: int = Field(0, description="是否带电(0否 1是)")
    goodstypecode: str = Field("WPX", description="货物类型")
    countrycode: str = Field(..., min_length=2, max_length=2, description="目的地国家")
    consigneecity: str = Field("", description="收件人城市")
    consigneezipcode: str = Field("", description="收件人邮编")

    @field_validator("countrycode", mode="before")
    @classmethod
    def uppercase_country(cls, v: str) -> str:
        return v.strip().upper() if isinstance(v, str) else v


class T6ChannelPriceDetail(BaseModel):
    amount: float = 0.0
    code: str = ""
    name: str = ""
    type: str = ""


class T6ChannelPriceResult(BaseModel):
    code: int = 0
    msg: str = ""
    amount: float = 0.0
    details: list[T6ChannelPriceDetail] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Query Price (searchPrice) — compare prices across channels
# ---------------------------------------------------------------------------

class PriceQueryRequest(BaseModel):
    dest: str = Field(..., min_length=1, description="目的地编码")
    desttype: str = Field("country", description="目的地类型(country/port/airport)")
    weight: float = Field(..., gt=0, description="总重量(KG)")
    piece: int = Field(1, gt=0, description="总件数")
    goodstype: str = Field("WPX", description="货物类型(WPX/DOC/PAK)")
    city: str = Field("", description="城市")
    zipcode: str = Field("", description="邮编")
    channelid: str = Field("", description="渠道代码(可选,不传查全部)")

    @field_validator("dest", mode="before")
    @classmethod
    def uppercase_dest(cls, v: str) -> str:
        return v.strip().upper() if isinstance(v, str) else v


class T6PriceChannel(BaseModel):
    channelid: str = ""
    channelname: str = ""
    channelnamecn: str = ""
    channelnameen: str = ""
    aging: str = ""
    note: str = ""


class T6PriceResult(BaseModel):
    channel: T6PriceChannel = Field(default_factory=T6PriceChannel)
    totalCost: float = 0.0
    totalCostCcy: str = "RMB"
    weight: float = 0.0
    tranCost: float = 0.0
    fuelCost: float = 0.0
    fuelCostRate: float = 0.0


# ---------------------------------------------------------------------------
# Query Channels
# ---------------------------------------------------------------------------

class T6Channel(BaseModel):
    channelid: str = ""
    channeltype: str = ""
    channelname: str = ""
    channelnamecn: str = ""
    channelnameen: str = ""


# ---------------------------------------------------------------------------
# Query Destinations
# ---------------------------------------------------------------------------

class DestQueryParams(BaseModel):
    desttype: str = Field("country", description="目的地类型(country/port/airport)")
    dest: str = Field("", description="目的地关键词")


class T6Destination(BaseModel):
    destName: str = ""
    destCode: str = ""


# ---------------------------------------------------------------------------
# Get Order Fees (orderRecSheets)
# ---------------------------------------------------------------------------

class OrderFeesRequest(BaseModel):
    waybillnumber: Optional[list[str]] = None

    @field_validator("waybillnumber", mode="before")
    @classmethod
    def wrap_single_str(cls, v: Any) -> Any:
        if isinstance(v, str):
            return [v]
        return v


class T6FeeItem(BaseModel):
    sheetid: str = ""
    costtype: str = ""
    costtypeName: str = ""
    amount: float = 0.0
    currency: str = ""
    currencyName: str = ""
    status: str = ""
    statusName: str = ""


class T6OrderFees(BaseModel):
    searchNumber: str = ""
    errormsg: str = ""
    inrweight: float = 0.0
    inmweight: float = 0.0
    clientweight: float = 0.0
    number: int = 0
    square: float = 0.0
    recsheetList: list[T6FeeItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Delete Order
# ---------------------------------------------------------------------------

class DeleteOrderRequest(BaseModel):
    """Delete by one of three number types."""
    customernumber: str = Field("", description="客户参考号1")
    waybillnumber: str = Field("", description="运单号")
    systemnumber: str = Field("", description="系统单号")


# ---------------------------------------------------------------------------
# Generic API error
# ---------------------------------------------------------------------------

class ApiError(BaseModel):
    code: str
    message: str
    retriable: bool = False

