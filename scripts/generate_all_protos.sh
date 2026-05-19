#!/bin/bash
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HERE}/.." && pwd)"

MS_DIRS=(
  "${REPO_ROOT}/ms-auth"
  "${REPO_ROOT}/ms-alumnos"
  "${REPO_ROOT}/ms-asistencias"
  "${REPO_ROOT}/ms-calificaciones"
  "${REPO_ROOT}/ms-notificaciones"
  "${REPO_ROOT}/ms-periodos"
  "${REPO_ROOT}/ms-reportes"
)

for ms in "${MS_DIRS[@]}"; do
  if [ -f "${ms}/generate_proto.sh" ]; then
    echo "Generando stubs en ${ms}..."
    (cd "${ms}" && bash ./generate_proto.sh)
  else
    echo "Aviso: no existe generate_proto.sh en ${ms}, se omite"
  fi
done

echo "Generación completada."
