#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Ensuring proto stubs (best-effort)"
if [ -x scripts/generate_all_protos.sh ]; then
  bash scripts/generate_all_protos.sh || true
fi

echo "Bringing up required services (build if needed)"
docker compose up --build -d ms-alumnos ms-auth ms-calificaciones ms-asistencias

echo "Waiting for services to become ready..."
sleep 5

echo "Running ms-calificaciones smoke test"
docker compose exec ms-calificaciones python scripts/test_calificaciones_client.py || {
  echo "ms-calificaciones smoke test failed" >&2
  exit 2
}

echo "Running ms-asistencias smoke test"
docker compose exec ms-asistencias python scripts/test_asistencias_client.py || {
  echo "ms-asistencias smoke test failed" >&2
  exit 3
}

echo "Smoke tests completed successfully"
