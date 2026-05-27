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

if [ "${AGM_RUN_MODE}" = "event-consumer" ]; then
  echo "Iniciando consumidor de eventos MS-6..."
  exec python manage.py run_event_consumer
fi

# Fase 5: sin gRPC de negocio entrante cuando el bus esta activo
if [ "${USE_EVENT_BUS}" != "true" ]; then
  echo "Iniciando servidor gRPC en puerto ${GRPC_PORT:-50056}..."
  python -m grpc_server.server &
fi

echo "Iniciando servidor REST en puerto ${REST_PORT}..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${REST_PORT} --workers 3 --timeout 120
