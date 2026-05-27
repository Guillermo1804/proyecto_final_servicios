#!/bin/bash
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MS_NAMES=(
  ms-auth
  ms-periodos
  ms-alumnos
  ms-calificaciones
  ms-asistencias
  ms-notificaciones
  ms-reportes
)

for ms in "${MS_NAMES[@]}"; do
  bash "${HERE}/generate_ms_proto.sh" "${ms}"
done

echo "Generacion completada (ver proto/README.md y scripts/proto_manifest.sh)."
