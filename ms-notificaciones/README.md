# MS-6 — Notificaciones (correo transaccional)

Microservicio Django + DRF para envío de correos y auditoría en `HistorialCorreo`. Expone **REST** (consumo vía gateway / Postman) y **gRPC** (MS-1, MS-3, MS-4).

## Puertos oficiales

| Protocolo | Puerto | Variable |
|-----------|--------|----------|
| REST (Gunicorn) | **8006** | `REST_PORT` |
| gRPC | **50056** | `GRPC_PORT` |

- Directo: `http://localhost:8006`
- Gateway Nginx: `http://localhost:8080/notificaciones/`
- Health: `GET /health/` → `{"status":"ok","service":"ms-notificaciones"}`

## Variables de entorno

Copiar `.env.example` → `.env`. **No commitear `.env`.**

### Base de datos

| Variable | Descripción |
|----------|-------------|
| `DB_HOST` | En Docker: `db-notificaciones` |
| `DB_NAME` | `agm_notificaciones_db` |

### SMTP (obligatorio para correo real)

| Variable | Descripción |
|----------|-------------|
| `EMAIL_HOST` | Ej. `smtp.gmail.com` |
| `EMAIL_PORT` | Ej. `587` |
| `EMAIL_USE_TLS` | `True` |
| `EMAIL_HOST_USER` | Cuenta emisor |
| `EMAIL_HOST_PASSWORD` | App Password (Gmail) o credencial del proveedor |
| `DEFAULT_FROM_EMAIL` | Remitente visible |
| `FRONTEND_URL` | Base para enlaces en plantillas (`http://localhost:4200`) |

### Seguridad REST

| Variable | Descripción |
|----------|-------------|
| `INTERNAL_API_KEY` | Cabecera `X-Internal-Api-Key` en llamadas servicio-a-servicio |
| `CORS_ALLOW_ALL_ORIGINS` | `True` en desarrollo; **`False` en producción** |
| `CORS_ALLOWED_ORIGINS` | Lista separada por comas si `CORS_ALLOW_ALL_ORIGINS=False` |

### Clientes gRPC externos (MS-6 como cliente)

| Variable | Servicio |
|----------|----------|
| `MS_AUTH_GRPC_HOST` / `MS_AUTH_GRPC_PORT` | MS-1 — `ValidateToken` |
| `MS_PERIODOS_GRPC_HOST` / `MS_PERIODOS_GRPC_PORT` | MS-2 — `GetMateriaById` |
| `MS_ALUMNOS_GRPC_HOST` / `MS_ALUMNOS_GRPC_PORT` | MS-3 — alumnos/docentes por materia |
| `GRPC_CLIENT_TIMEOUT` | Timeout en segundos (default `5`) |
| `USE_PLACEHOLDER_DATA` | `True` solo tests; `False` en Docker/producción |

### Servidor gRPC propio

| Variable | Descripción |
|----------|-------------|
| `GRPC_MAX_WORKERS` | Hilos del pool gRPC (default `10`) |
| `EMAIL_MAX_WORKERS` | Hilos envío masivo cierre materia (default `5`) |

## Endpoints REST

Prefijo: `/notificaciones/` (todos **POST**, requieren `X-Internal-Api-Key` o JWT admin).

| Ruta | Body JSON |
|------|-----------|
| `bienvenida` | `alumno_id`, `materia_id`, `clave_acceso` |
| `baja` | `alumno_id`, `docente_id`, `materia_id` |
| `cierre-materia` | `materia_id` |
| `reset-password` | `email`, `token`, `reset_url` |

Respuesta envelope AGM: `{ "success", "data", "message", "errors" }`.

## Servidor gRPC (`proto/notificaciones.proto`)

| RPC | Puerto |
|-----|--------|
| `SendBienvenida` | 50056 |
| `SendBajaNotif` | |
| `SendCierreMateria` | |
| `SendResetPassword` | |

Arranque en Docker: `python -m grpc_server.server &` (ver `entrypoint.sh`).

Prueba local con proto:

```bash
grpcurl -plaintext -import-path ../proto -proto notificaciones.proto \
  localhost:50056 list
```

## Comandos útiles

```bash
# Desde la raíz del monorepo
docker compose up --build -d ms-notificaciones

docker exec agm-ms-notificaciones python manage.py test apps.notificaciones.tests -v 2
docker exec agm-ms-notificaciones python manage.py send_test_email --to tu@correo.com
docker exec agm-ms-notificaciones python manage.py migrate
```

## Consumidores integrados (Epic 8 / Fase F)

| MS | Uso |
|----|-----|
| MS-1 | `SendResetPassword` en forgot-password |
| MS-3 | `SendBienvenida`, `SendBajaNotif` |
| MS-4 | `SendCierreMateria` tras `POST /materias/:id/cerrar` |

Variables en consumidores: `MS_NOTIFICACIONES_GRPC_HOST=ms-notificaciones`, `MS_NOTIFICACIONES_GRPC_PORT=50056`.

## Postman

Carpeta **MS-6 Notificaciones** en [`docs/postman/AGM_API_Collection.json`](../docs/postman/AGM_API_Collection.json).  
Environment: `base_url_gateway`, `internal_api_key`.

## Documentación relacionada

- [`docs/microservicios/MS6_NOTIFICACIONES.md`](../docs/microservicios/MS6_NOTIFICACIONES.md)
- [`docs/devs/Makinohara/PLAN_ACCION_MS6_NOTIFICACIONES.md`](../docs/devs/Makinohara/PLAN_ACCION_MS6_NOTIFICACIONES.md)
- [`docs/RESUMEN_CAMBIOS.md`](../docs/RESUMEN_CAMBIOS.md) (pulido MS-6, casos P1–P10)

## Producción

- `CORS_ALLOW_ALL_ORIGINS=False` y orígenes explícitos en `CORS_ALLOWED_ORIGINS`.
- SMTP y `INTERNAL_API_KEY` solo en variables del proveedor (Railway, etc.).
- Ver [`docs/devs/Makinohara/DESPLIEGUE_RAILWAY.md`](../docs/devs/Makinohara/DESPLIEGUE_RAILWAY.md).
