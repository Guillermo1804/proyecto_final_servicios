#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROTO_ROOT="${REPO_ROOT}/proto"
OUT_DIR="${SCRIPT_DIR}/proto_generated"

mkdir -p "${OUT_DIR}"

# Genera los stubs para el servidor de notificaciones y sus dependencias de mensajes
python -m grpc_tools.protoc -I"${PROTO_ROOT}" \
  --python_out="${OUT_DIR}" \
  --grpc_python_out="${OUT_DIR}" \
  "${PROTO_ROOT}/notificaciones.proto" \
  "${PROTO_ROOT}/auth.proto" \
  "${PROTO_ROOT}/alumnos.proto" \
  "${PROTO_ROOT}/periodos.proto"

echo "Stubs generados en ${OUT_DIR}/"
