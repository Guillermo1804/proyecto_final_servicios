#!/bin/bash
# Espera a que un puerto gRPC TCP esté escuchando (uso en entrypoint.sh).
PORT="${1:-50051}"
MAX_ATTEMPTS="${2:-45}"

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  if python -c "
import socket
import sys
port = int('${PORT}')
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect(('127.0.0.1', port))
    s.close()
    sys.exit(0)
except OSError:
    sys.exit(1)
"; then
    echo "gRPC escuchando en puerto ${PORT} (intento ${attempt})."
    exit 0
  fi
  sleep 1
done

echo "ERROR: gRPC no disponible en puerto ${PORT} tras ${MAX_ATTEMPTS}s."
exit 1
