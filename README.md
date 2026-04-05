# Logistics ADK Agent

基于 [Google ADK](https://google.github.io/adk-docs/) 构建的跨境物流智能助手，包含 **AI Agent 后端**（FastAPI + Multi-Agent）和 **Web 前端**（Next.js）。

```
┌─────────────┐    ┌──────────────────────────────────────────┐    ┌────────────┐
│  Frontend   │───▶│  Backend (FastAPI)                       │───▶│ PostgreSQL │
│  Next.js    │    │  ├─ Auth (JWT)                           │    └────────────┘
│  Port 3000  │    │  ├─ Chat (SSE streaming)                 │
└─────────────┘    │  └─ Agent (Google ADK)                   │
                   │     ├─ order_agent    → 3 tools          │
                   │     ├─ tracking_agent → 2 tools          │
                   │     └─ pricing_agent  → 4 tools          │
                   │                        Port 8000         │
                   └──────────────────────────────────────────┘
```

## 快速启动（Docker Compose）

```bash
# 1. 复制环境变量模板
cp .env.example .env
# 编辑 .env，填入 GOOGLE_API_KEY 等

# 2. 一键启动
docker compose up -d

# 3. 访问
# 前端: http://localhost:3000
# 后端: http://localhost:8000/docs
```

## 本地开发

### 后端

```bash
cd backend
cp .env.example .env        # 编辑 .env
uv sync --extra dev         # 安装依赖
alembic upgrade head        # 数据库迁移
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev                 # http://localhost:3000
```

详见 [backend/README.md](backend/README.md) 了解架构设计与 Agent 详情。

## 项目结构

```
logistics-adk-agent/
├── .env                    # 环境变量（不提交）
├── .env.example            # 环境变量模板
├── docker-compose.yml      # 一键部署 (db + backend + frontend)
├── backend/                # Python 后端
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── agent/              # Google ADK Multi-Agent 系统
│   ├── app/                # FastAPI Web 服务
│   ├── alembic/            # 数据库迁移
│   └── tests/
└── frontend/               # Next.js 前端
    ├── Dockerfile
    ├── package.json
    └── src/
```
