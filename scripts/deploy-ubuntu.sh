#!/usr/bin/env bash
# Despliegue completo AGM en Ubuntu (VPS / Coolify manual).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Instala Docker Engine y el plugin Compose primero."
  exit 1
fi

if [[ ! -f ms-auth/.env ]]; then
  echo "Copiando .env desde .env.example en cada microservicio..."
  for d in ms-auth ms-periodos ms-alumnos ms-calificaciones ms-asistencias ms-notificaciones ms-reportes; do
    cp "$d/.env.example" "$d/.env"
  done
fi

[[ -f .env ]] || cp .env.example .env

echo "Build y arranque (prod overlay, sin bind de puertos en el host)..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo ""
echo "OK. En Coolify asigna el dominio al servicio nginx, puerto del contenedor 80 (no uses 80:80 en Compose)."
echo "Migraciones: ver docs/DEPLOY_COOLIFY.md"
