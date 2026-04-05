# ── Frontend Dockerfile (Next.js) ────────────────────────────────────
#
# Build args (set via Render environment variables):
#   BACKEND_URL          — backend origin for Next.js rewrite proxy
#                          e.g. "https://logistics-backend.onrender.com"
#   NEXT_PUBLIC_API_URL  — (alternative) client-side direct mode
#                          e.g. "https://logistics-backend.onrender.com/api"
#
# If neither is set, the frontend falls back to /api → localhost:8000.
# ─────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and build
COPY . .

# Ensure public/ exists (git doesn't track empty directories)
RUN mkdir -p public

# Accept build args so next.config.js rewrites and NEXT_PUBLIC_ inlining
# pick up the correct values during `next build`.
ARG BACKEND_URL
ARG NEXT_PUBLIC_API_URL
ENV BACKEND_URL=$BACKEND_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# ── Runtime stage ────────────────────────────────────────────────────
FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js ./

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

EXPOSE 3000

CMD ["npm", "start"]
