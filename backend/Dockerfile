# ── Backend Dockerfile (uv + FastAPI) ────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Install dependencies first (cache-friendly)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY . .
RUN uv sync --frozen --no-dev

# ── Runtime stage ────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Run alembic migrations then start uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

