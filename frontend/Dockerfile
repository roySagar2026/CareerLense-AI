# Build from the REPOSITORY ROOT (nginx config lives in infrastructure/nginx):
#   docker build -f frontend/Dockerfile -t careerlens-frontend .
FROM node:22-alpine AS build
WORKDIR /app/frontend

# package-lock.json is copied when present (commit it after your first `npm install`).
COPY frontend/package.json frontend/package-lock.jso[n] ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY frontend/ ./
# Same-origin API path by default; override with --build-arg VITE_API_BASE_URL=...
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Unprivileged nginx runs as a non-root user and listens on 8080.
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY infrastructure/nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY infrastructure/nginx/security-headers.conf /etc/nginx/security-headers.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO /dev/null http://127.0.0.1:8080/ || exit 1
