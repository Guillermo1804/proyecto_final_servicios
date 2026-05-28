# Gateway AGM: Angular (producción) + reverse proxy a MS-1…MS-7
# Build context: raíz del monorepo (docker compose build nginx)

FROM node:22-alpine AS frontend-build
WORKDIR /app

COPY frontend/sistema_AGM/package.json frontend/sistema_AGM/package-lock.json* ./
RUN npm ci

COPY frontend/sistema_AGM/ ./
RUN npm run build -- --configuration production

FROM nginx:1.25-alpine

COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /app/dist/sistema_AGM/browser /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=10s \
  CMD wget -q -O - http://127.0.0.1/health | grep -q ok
