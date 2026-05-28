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
echo "Claves JWT RSA (RS256)..."
python manage.py ensure_jwt_keys

echo "Aplicando migraciones..."
python manage.py migrate --noinput

# Crear usuario administrador inicial solo en API principal (no workers)
if [ -z "${AGM_RUN_MODE}" ]; then
  echo "Inicializando administrador..."
  python manage.py create_admin
fi

# Modos worker (Fase 2+) — docker-compose define AGM_RUN_MODE
if [ "${AGM_RUN_MODE}" = "outbox-worker" ]; then
  echo "Iniciando relay outbox → RabbitMQ..."
  exec python manage.py run_event_outbox
fi

if [ "${AGM_RUN_MODE}" = "event-consumer" ]; then
  echo "Iniciando consumidor de eventos MS-1..."
  exec python manage.py run_event_consumer
fi

# Arrancar servidor gRPC en background (si existe el management command)
if python manage.py help grpc_server 2>/dev/null; then
  echo "Iniciando servidor gRPC en puerto ${GRPC_PORT}..."
  python manage.py grpc_server &
fi

# Arrancar Gunicorn
echo "Iniciando servidor REST en puerto ${REST_PORT}..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${REST_PORT} --workers 3 --timeout 120