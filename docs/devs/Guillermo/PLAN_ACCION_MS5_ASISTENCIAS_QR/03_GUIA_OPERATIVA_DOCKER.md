# 03 - Guia operativa Docker

## 1) Precondiciones

- Docker y Docker Compose instalados.
- Variables de entorno cargadas para MS-5 (usar `.env.example` como base).
- Servicios dependientes disponibles en red de docker:
  - MySQL
  - Redis
  - ms-auth (gRPC)
  - ms-alumnos (gRPC)

## 2) Variables de entorno criticas

Referencia: `ms-asistencias/.env.example`

Obligatorias:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `REDIS_HOST`, `REDIS_PORT`
- `REST_PORT` (esperado: 8005)
- `GRPC_PORT` (esperado: 50055)
- `QR_HMAC_SECRET`

Dependencias gRPC salientes:
- `MS_AUTH_GRPC_HOST`, `MS_AUTH_GRPC_PORT`
- `MS_ALUMNOS_GRPC_HOST`, `MS_ALUMNOS_GRPC_PORT`

## 3) Arranque del servicio

El `entrypoint.sh` hace lo siguiente automaticamente:
1. Espera MySQL.
2. Ejecuta migraciones (`python manage.py migrate --noinput`).
3. Levanta servidor gRPC en background (`python manage.py grpc_server`).
4. Levanta Gunicorn para REST.

Comando sugerido (desde raiz del repo):

```bash
docker compose up -d --build ms-asistencias
```

## 4) Verificacion post-arranque

### Ver logs de MS-5

```bash
docker compose logs -f ms-asistencias
```

Esperado:
- Mensaje de MySQL listo.
- Migraciones aplicadas.
- Mensaje de gRPC iniciado en 50055.
- Gunicorn escuchando en 8005.

### Verificar REST

```bash
curl http://localhost:8005/health/
```

### Verificar gRPC (nivel proceso)

En logs debe verse la linea del comando `grpc_server` iniciado. Si no aparece, revisar `entrypoint.sh` y `apps/core/management/commands/grpc_server.py`.

## 5) Flujo operativo recomendado (manual)

1. Iniciar sesion de asistencia:
```http
POST /api/sesiones/iniciar/
```

2. Generar QR para alumno:
```http
GET /api/qr/generate/?materia_id=...&alumno_id=...
```

3. Registrar asistencia:
```http
POST /api/asistencias/registrar/
```

4. Consultar stats en vivo:
```http
GET /api/sesiones/{id}/stats/
```

5. Cerrar o confirmar sesion:
```http
DELETE /api/sesiones/{id}/cerrar/
POST   /api/sesiones/{id}/confirmar/
POST   /api/sesiones/{id}/solicitar-nueva/
```

## 6) Notas operativas importantes

- El tiempo de validez del QR depende del reloj del servidor. En contenedores desfasados puede fallar la validacion de timestamp.
- Redis es critico para anti-replay y estado temporal de sesion.
- MySQL es la fuente de verdad para historico y gRPC.
- gRPC se levanta en paralelo al REST dentro del mismo contenedor.
