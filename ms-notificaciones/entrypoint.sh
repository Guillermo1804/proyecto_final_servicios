#!/bin/bash
set -e

echo "Esperando a que MySQL este listo..."
while ! python -c "
import MySQLdb
MySQLdb.connect(
    host='${DB_HOST}',
    port=int('${DB_PORT}'),
    user='${DB_USER}',
    passwd='${DB_PASSWORD}',
    db='${DB_NAME}'
)" 2>/dev/null; do
  echo "  MySQL no disponible, reintentando en 2s..."
  sleep 2
done
echo "MySQL listo!"

# Aplicar migraciones
echo "Aplicando migraciones..."
python manage.py migrate --noinput

# Arrancar servidor gRPC en background (puerto GRPC_PORT, default 50056)
echo "Iniciando servidor gRPC en puerto ${GRPC_PORT:-50056}..."
python -m grpc_server.server &

# Arrancar Gunicorn
echo "Iniciando servidor REST en puerto ${REST_PORT}..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${REST_PORT} --workers 3 --timeout 120