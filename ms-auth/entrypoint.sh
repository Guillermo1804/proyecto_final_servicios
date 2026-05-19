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

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Inicializando administrador..."
python manage.py create_admin

GRPC_PORT="${GRPC_PORT:-50051}"
echo "Iniciando servidor gRPC en puerto ${GRPC_PORT}..."
nohup python manage.py grpc_server >/tmp/grpc-ms-auth.log 2>&1 &
echo "gRPC PID $!"
bash /docker/scripts/wait_grpc_port.sh "${GRPC_PORT}" 45

echo "Iniciando servidor REST en puerto ${REST_PORT}..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${REST_PORT} --workers 3 --timeout 120
