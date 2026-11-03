# Dockerfile for React frontend (apps/web/Dockerfile)
# Multi‑stage build: node for building, nginx for serving static files

# ---------- Build stage ----------
FROM node:20-alpine AS builder
WORKDIR /app

# Install pnpm (as required by tech stack)
RUN npm i -g pnpm

COPY apps/web/package.json .
COPY apps/web/pnpm-lock.yaml .
COPY apps/web/tsconfig.json .
COPY apps/web/vite.config.ts .
COPY apps/web/.npmrc .
COPY apps/web/src ./src
COPY apps/web/public ./public

RUN pnpm install --frozen-lockfile
RUN pnpm run build

# ---------- Production stage ----------
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;" ]
