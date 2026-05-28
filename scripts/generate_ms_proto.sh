#!/bin/bash
set -e

MS_DIR_NAME="${1:-}"
if [ -z "${MS_DIR_NAME}" ]; then
  echo "Uso: bash scripts/generate_ms_proto.sh <ms-auth|ms-periodos|...>" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MS_DIR="${REPO_ROOT}/${MS_DIR_NAME}"
PROTO_ROOT="${REPO_ROOT}/proto"
OUT_DIR="${MS_DIR}/proto_generated"

# shellcheck source=proto_manifest.sh
source "${SCRIPT_DIR}/proto_manifest.sh"

if [ ! -d "${MS_DIR}" ]; then
  echo "No existe directorio ${MS_DIR}" >&2
  exit 1
fi

read -r -a PROTO_FILES <<< "$(proto_files_for_ms "${MS_DIR_NAME}")"

mkdir -p "${OUT_DIR}"

rm -f "${OUT_DIR}"/*_pb2.py "${OUT_DIR}"/*_pb2_grpc.py 2>/dev/null || true

ARGS=()
for f in "${PROTO_FILES[@]}"; do
  ARGS+=("${PROTO_ROOT}/${f}")
done

PYTHON_ARGS=()
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
else
  PYTHON_BIN=py
  PYTHON_ARGS=(-3)
fi

"${PYTHON_BIN}" "${PYTHON_ARGS[@]}" -m grpc_tools.protoc -I"${PROTO_ROOT}" \
  --python_out="${OUT_DIR}" \
  --grpc_python_out="${OUT_DIR}" \
  "${ARGS[@]}"

echo "${MS_DIR_NAME}: stubs -> ${OUT_DIR}/ (${PROTO_FILES[*]})"
