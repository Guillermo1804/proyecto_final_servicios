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
  echo "Iniciando consumidor de eventos MS-4..."
  exec python manage.py run_event_consumer
fi

if [ "${AGM_RUN_MODE}" = "event-outbox" ]; then
  echo "Iniciando relay outbox MS-4..."
  exec python manage.py run_event_outbox
fi

if [ "${USE_EVENT_BUS}" != "true" ]; then
  if python manage.py help grpc_server 2>/dev/null; then
    echo "Iniciando servidor gRPC en puerto ${GRPC_PORT}..."
    python manage.py grpc_server &
  fi
fi

echo "Iniciando servidor REST en puerto ${REST_PORT}..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${REST_PORT} --workers 3 --timeout 120
