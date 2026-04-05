# ── Frontend Dockerfile (Next.js) ────────────────────────────────────
#
# Build-time env: NEXT_PUBLIC_API_URL (the backend's public URL)
#   docker build --build-arg NEXT_PUBLIC_API_URL=https://api.example.com/api .
#
# If not set, the frontend falls back to /api (dev proxy mode).
# ─────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and build
COPY . .

# Accept the backend URL as a build arg so Next.js can inline it into
# the client bundle via the NEXT_PUBLIC_ prefix convention.
ARG NEXT_PUBLIC_API_URL
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
