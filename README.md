# Logistics ADK Agent

基于 [Google ADK](https://google.github.io/adk-docs/) 构建的物流操作智能体，能够与物流 API 交互，完成查询订单状态、查询运单、创建货运单和估算运价等功能。

示例对话：

- "查询订单 #12345 的运输状态"
- "创建从深圳到洛杉矶的新货运单"

API 文档：http://47.115.60.18/api/doc

---

## 架构设计

```
用户 ──▶ Agent 层 ──▶ Tool 层 ──▶ Service 层 ──▶ Provider 层
              │                        │                │
          意图解析/决策          校验/格式化       Mock / HTTP
```

| 层 | 职责 |
|---|---|
| **Agent** | 接收用户输入，解析意图，调用工具 |
| **Tool** | 四个工具函数：查询订单运输状态、查询运单状态、创建货运单、估算运价 |
| **Service** | 统一校验、响应格式化、业务编排，隔离 Provider 细节 |
| **Provider** | `MockLogisticsProvider` 提供可重复的模拟数据；`HttpLogisticsProvider` 接入真实系统 |
| **Domain** | Pydantic 模型，定义货运单等核心数据结构 |

设计原则：

1. Agent 保持轻量，专注解析和决策
2. 工具保持单一职责，明确类型
3. 不引入持久化

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
LOGISTICS_API_BASE_URL=https://example-logistics-api.local
LOGISTICS_API_KEY=replace-me
LOGISTICS_HTTP_TIMEOUT_SECONDS=10
```

| 变量 | 说明 | 默认值 |
|---|---|---|
| `GOOGLE_API_KEY` | Google Gemini API Key | — |
| `GOOGLE_GENAI_USE_VERTEXAI` | 是否使用 Vertex AI | `0` |
| `LOGISTICS_PROVIDER_BACKEND` | 数据源：`mock` 或 `http` | `mock` |
| `LOGISTICS_AGENT_MODEL` | 使用的模型 | `gemini-3-flash-preview` |
| `LOGISTICS_API_BASE_URL` | HTTP Provider 的 API 地址 | — |
| `LOGISTICS_API_KEY` | HTTP Provider 的 API Key | — |
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

直接调用工具函数，输出 JSON 结果，用于验证 Provider 和 Service 层是否正常。

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
| `test_domain_validation.py` | Domain 模型校验（非法运输模式、非正数重量等） |
| `test_logistics_service.py` | Service 层核心逻辑（订单追踪、创建运单、报价、错误格式化） |

示例输出：

```
tests/test_domain_validation.py::test_create_shipment_request_rejects_invalid_mode  PASSED
tests/test_domain_validation.py::test_rate_quote_rejects_non_positive_weight        PASSED
tests/test_logistics_service.py::test_track_existing_order                          PASSED
tests/test_logistics_service.py::test_create_shipment                               PASSED
tests/test_logistics_service.py::test_quote_rate                                    PASSED
tests/test_logistics_service.py::test_format_validation_error_is_structured         PASSED
tests/test_logistics_service.py::test_format_internal_error                         PASSED
========================= 7 passed =========================
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
├── .env                          # 环境变量配置
├── pyproject.toml                # 项目元数据与依赖
├── README.md
├── logistics_agent/
│   ├── __init__.py               # 入口，导入 agent 模块
│   ├── agent.py                  # ADK Agent 定义（root_agent）
│   ├── config.py                 # 配置加载（dotenv + Settings）
│   ├── main.py                   # CLI 快速测试脚本
│   ├── models/
│   │   └── domain.py             # Pydantic 数据模型
│   ├── providers/
│   │   ├── base.py               # Provider 抽象基类
│   │   ├── factory.py            # Provider 工厂
│   │   ├── mock_provider.py      # Mock 数据源
│   │   └── http_provider.py      # HTTP 数据源（骨架）
│   ├── services/
│   │   └── logistics_service.py  # 业务逻辑层
│   ├── tools/
│   │   └── logistics_tools.py    # ADK Tool 函数
│   └── utils/
│       └── presenters.py         # 展示工具
└── tests/
    ├── test_domain_validation.py # Domain 模型测试
    └── test_logistics_service.py # Service 层测试
```
