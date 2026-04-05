# Logistics ADK Agent

基于 [Google ADK](https://google.github.io/adk-docs/) 构建的跨境物流操作智能体，能够与物流 API 交互，完成**查询订单状态**、**查询运单**、**创建货运单**和**估算运价**等功能。

示例对话：

- "帮我查一下运单 T6W20260401002 的轨迹"
- "10KG 包裹发美国，各渠道报价对比一下"
- "用 DHL 渠道创建一个发往英国的运单"
- "查一下最近一周的运单列表"

API 文档：http://47.115.60.18/api/doc

---

## 架构设计

### Multi-Agent 架构

```
用户 ──▶ root_agent (总调度) ──┬──▶ order_agent    ──▶ Tool ──▶ Service ──▶ Provider
                             ├──▶ tracking_agent  ──▶ Tool ──▶ Service ──▶ Provider
                             └──▶ pricing_agent   ──▶ Tool ──▶ Service ──▶ Provider
```

| 智能体 | 职责 | 工具数 |
|---|---|---|
| **root_agent** | 总调度：理解用户意图，路由到合适的子智能体 | — |
| **order_agent** | 订单管理：创建运单、查询运单列表、删除运单 | 3 |
| **tracking_agent** | 物流追踪：运单轨迹查询、费用明细查询 | 2 |
| **pricing_agent** | 报价询价：运费试算、多渠道比价、渠道/目的地查询 | 4 |

### 分层架构

| 层 | 职责 |
|---|---|
| **Agent** | Multi-Agent 协作，root_agent 路由 → 子 agent 执行 |
| **Tool** | 9 个工具函数，按职责分布在 3 个子智能体中 |
| **Service** | 统一校验、响应格式化、业务编排，隔离 Provider 细节 |
| **Provider** | `MockLogisticsProvider` 提供模拟数据；`HttpLogisticsProvider` 对接真实物流系统 API |
| **Domain** | Pydantic 模型，与物流系统 API JSON 结构对齐 |

### 子智能体与工具映射

#### order_agent — 订单管理

| 工具 | 对应 API | 说明 |
|---|---|---|
| `create_order` | `POST /api/order/createForecast` | 创建运单（下单到预报） |
| `query_orders` | `POST /api/order/pageOrders` | 按日期分页查询运单列表 |
| `delete_order` | `POST /api/order/delete` | 删除运单 |

#### tracking_agent — 物流追踪

| 工具 | 对应 API | 说明 |
|---|---|---|
| `track_shipment` | `POST /api/track` | 查询轨迹与订单状态（支持运单号/系统单号/客户参考号） |
| `get_order_fees` | `POST /api/order/recsheet` | 查询运单费用明细 |

#### pricing_agent — 报价询价

| 工具 | 对应 API | 说明 |
|---|---|---|
| `estimate_shipping_cost` | `POST /api/searchChannelPrice` | 指定渠道运费试算 |
| `query_price` | `POST /api/searchPrice` | 多渠道报价对比 |
| `query_channels` | `POST /api/order/channel` | 查询可用渠道 |
| `query_destinations` | `GET /api/searchDest` | 查询目的地 |

### 设计原则

1. **关注点分离**：每个子智能体只关注自己的领域
2. **root_agent 不持有工具**：只负责路由，避免工具过载
3. **工具保持单一职责**：一个函数 = 一个 API 能力
4. **Mock 数据格式与真实 API 一致**：方便在 Mock / HTTP 之间切换

---

## 环境要求

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/)（推荐）或 pip

---

## 安装

### 使用 uv（推荐）

```bash
# 克隆项目
git clone https://github.com/caoshengdong/logistics-adk-agent.git
cd logistics-adk-agent

# 创建虚拟环境并安装依赖
uv sync

# 如需开发依赖（pytest / ruff / mypy）
uv sync --extra dev
```

### 使用 pip

```bash
cd logistics-adk-agent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

# 如需开发依赖
pip install -e ".[dev]"
```

---

## 配置

在**项目根目录**创建 `.env` 文件：

```dotenv
# Gemini API 配置
GOOGLE_GENAI_USE_VERTEXAI=0
GOOGLE_API_KEY=your-google-api-key

# Provider 选择：mock（默认）或 http
LOGISTICS_PROVIDER_BACKEND=mock

# 以下仅在 LOGISTICS_PROVIDER_BACKEND=http 时需要
LOGISTICS_API_BASE_URL=http://47.115.60.18
LOGISTICS_AUTH_CODE=your-client-code
LOGISTICS_AUTH_TOKEN=your-api-token
LOGISTICS_HTTP_TIMEOUT_SECONDS=10
```

| 变量 | 说明 | 默认值 |
|---|---|---|
| `GOOGLE_API_KEY` | Google Gemini API Key | — |
| `GOOGLE_GENAI_USE_VERTEXAI` | 是否使用 Vertex AI | `0` |
| `LOGISTICS_PROVIDER_BACKEND` | 数据源：`mock` 或 `http` | `mock` |
| `LOGISTICS_AGENT_MODEL` | 使用的模型 | `gemini-2.0-flash` |
| `LOGISTICS_API_BASE_URL` | 物流系统 API 地址 | `http://47.115.60.18` |
| `LOGISTICS_AUTH_CODE` | 客户编码 | — |
| `LOGISTICS_AUTH_TOKEN` | API 授权码 | — |
| `LOGISTICS_HTTP_TIMEOUT_SECONDS` | HTTP 请求超时（秒） | `10` |

---

## 运行

### 启动 Web UI

```bash
adk web --host localhost .
```

然后在浏览器打开 http://localhost:8000。

> **注意**：请使用 `--host localhost` 启动，避免浏览器 Origin 校验导致 403 错误。

### 命令行快速测试（不依赖 Gemini）

```bash
python -m logistics_agent.main
```

直接调用全部 9 个工具函数，输出 JSON 结果，用于验证 Provider 和 Service 层是否正常。

---

## 测试

项目使用 [pytest](https://docs.pytest.org/) 作为测试框架，测试文件位于 `tests/` 目录。

### 运行全部测试

```bash
python -m pytest tests/ -v
```

### 测试覆盖

| 测试文件 | 覆盖内容 |
|---|---|
| `test_domain_validation.py` | Domain 模型校验（必填字段、零值重量、国家码大写、页码校验等） |
| `test_logistics_service.py` | Service 层全部 9 个方法 + 错误格式化（完整生命周期测试） |

示例输出：

```
tests/test_domain_validation.py::test_create_order_request_validates_required_fields    PASSED
tests/test_domain_validation.py::test_create_order_request_rejects_zero_weight          PASSED
tests/test_domain_validation.py::test_create_order_request_uppercases_country           PASSED
tests/test_domain_validation.py::test_channel_price_request_rejects_empty_channelid     PASSED
tests/test_domain_validation.py::test_price_query_request_rejects_zero_weight           PASSED
tests/test_domain_validation.py::test_track_request_wraps_single_string                 PASSED
tests/test_domain_validation.py::test_query_orders_request_rejects_zero_page            PASSED
tests/test_logistics_service.py::test_query_channels                                    PASSED
tests/test_logistics_service.py::test_query_destinations_all                            PASSED
tests/test_logistics_service.py::test_query_destinations_filter                         PASSED
tests/test_logistics_service.py::test_query_price                                       PASSED
tests/test_logistics_service.py::test_estimate_channel_price                            PASSED
tests/test_logistics_service.py::test_create_order                                      PASSED
tests/test_logistics_service.py::test_query_orders                                      PASSED
tests/test_logistics_service.py::test_track_shipment_by_waybill                         PASSED
tests/test_logistics_service.py::test_track_shipment_by_systemnumber                    PASSED
tests/test_logistics_service.py::test_track_shipment_not_found                          PASSED
tests/test_logistics_service.py::test_get_order_fees                                    PASSED
tests/test_logistics_service.py::test_get_order_fees_not_found                          PASSED
tests/test_logistics_service.py::test_delete_order_predicted_status                     PASSED
tests/test_logistics_service.py::test_delete_order_shipped_status                       PASSED
tests/test_logistics_service.py::test_delete_order_not_found                            PASSED
tests/test_logistics_service.py::test_format_validation_error                           PASSED
tests/test_logistics_service.py::test_format_internal_error                             PASSED
========================= 24 passed =========================
```

### 代码检查（可选）

```bash
# Lint
ruff check .

# 类型检查
mypy logistics_agent/
```

---

## 项目结构

```
logistics-adk-agent/
├── .env                          # 环境变量配置（不提交到 Git）
├── pyproject.toml                # 项目元数据与依赖
├── README.md
├── logistics_agent/
│   ├── __init__.py               # 入口，导入 agent 模块
│   ├── agent.py                  # Multi-Agent 定义（root + 3 个子智能体）
│   ├── config.py                 # 配置加载（dotenv + Settings）
│   ├── main.py                   # CLI 快速测试脚本
│   ├── models/
│   │   └── domain.py             # Pydantic 数据模型（与物流系统 API 对齐）
│   ├── providers/
│   │   ├── base.py               # Provider 抽象基类（9 个抽象方法）
│   │   ├── factory.py            # Provider 工厂
│   │   ├── mock_provider.py      # Mock 数据源
│   │   └── http_provider.py      # HTTP 数据源（httpx）
│   ├── services/
│   │   └── logistics_service.py  # 业务逻辑层
│   ├── tools/
│   │   ├── _common.py            # 共享 Service 单例
│   │   ├── order_tools.py        # 订单工具（create / query / delete）
│   │   ├── tracking_tools.py     # 追踪工具（track / fees）
│   │   └── pricing_tools.py      # 报价工具（estimate / price / channels / dest）
│   └── utils/
│       └── presenters.py         # 展示工具
└── tests/
    ├── test_domain_validation.py # Domain 模型测试
    └── test_logistics_service.py # Service 层测试（24 个用例）
```
