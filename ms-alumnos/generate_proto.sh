#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROTO_ROOT="${REPO_ROOT}/proto"
OUT_DIR="${SCRIPT_DIR}/proto_generated"

mkdir -p "${OUT_DIR}"

python -m grpc_tools.protoc -I"${PROTO_ROOT}" \
	--python_out="${OUT_DIR}" \
	--grpc_python_out="${OUT_DIR}" \
	"${PROTO_ROOT}/alumnos.proto"

echo "Stubs generados en ${OUT_DIR}/"
