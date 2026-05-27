#!/usr/bin/env bash
# Reconciliación idempotente de proyecciones (MS-3, MS-4, MS-5) con BD fuente.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Reconciliando proyecciones MS-3, MS-4, MS-5..."
docker compose exec ms-alumnos python manage.py reconcile_projections
docker compose exec ms-calificaciones python manage.py reconcile_projections
docker compose exec ms-asistencias python manage.py reconcile_projections
echo "Listo."
