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

# Crear usuario administrador inicial
echo "Inicializando administrador..."
python manage.py create_admin

# Arrancar servidor gRPC en background (si existe el management command)
if python manage.py help grpc_server 2>/dev/null; then
  echo "Iniciando servidor gRPC en puerto ${GRPC_PORT}..."
  python manage.py grpc_server &
fi

# Arrancar Gunicorn
echo "Iniciando servidor REST en puerto ${REST_PORT}..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${REST_PORT} --workers 3 --timeout 120