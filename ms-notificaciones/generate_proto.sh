#!/bin/bash
# Genera stubs de los protos que consume MS-6 (clientes salientes + servidor propio).
set -e
PROTO_DIR="../proto"
OUT_DIR="./proto_generated"

python -m grpc_tools.protoc -I"${PROTO_DIR}" \
  --python_out="${OUT_DIR}" \
  --grpc_python_out="${OUT_DIR}" \
  "${PROTO_DIR}/notificaciones.proto" \
  "${PROTO_DIR}/auth.proto" \
  "${PROTO_DIR}/alumnos.proto" \
  "${PROTO_DIR}/periodos.proto"

echo "Stubs generados en ${OUT_DIR}/"
