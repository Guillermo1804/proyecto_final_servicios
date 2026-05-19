# MS-5 — Asistencias QR

Sesiones de pase de lista (10 min), tokens QR firmados (HMAC), registro con anti-replay (Redis) y **gRPC** para MS-7.

## Puertos

| Protocolo | Puerto |
|-----------|--------|
| REST | **8005** |
| gRPC | **50055** |

Gateway: `/sesiones/`, `/registros/`, `/qr/generate/`, `/asistencias/registrar/`.

## Variables de entorno

Ver `.env.example`. Requiere **MySQL** (`agm_asistencias_db`), **Redis** y clientes gRPC: MS-1 (auth), MS-3 (`IsAlumnoEnMateria`).

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/sesiones/iniciar/` | Abre sesión (una activa por materia) |
| GET | `/sesiones/activa/?materia_id=` | Sesión vigente |
| GET | `/sesiones/{id}/stats/` | Presentes / retardos / ausentes |
| DELETE | `/sesiones/{id}/cerrar/` | Cierra sesión |
| GET | `/qr/generate/?materia_id=&alumno_id=` | Payload QR (30 s) |
| POST | `/asistencias/registrar/` | Escaneo docente (`encoded_payload`) |
| GET | `/registros/?sesion_id=` | Listado en vivo (`alumno_nombre`, `matricula` vía MS-3) |

Autenticación: **Bearer JWT** validado vía gRPC MS-1 (`MsJwtAuthentication`).

## Desarrollo

```bash
docker compose up -d ms-asistencias db-asistencias redis ms-auth ms-alumnos
docker compose build ms-asistencias
docker exec agm-ms-asistencias python manage.py test apps.core.tests tests.test_grpc_utils

# Cerrar sesiones expiradas (cron / manual)
docker exec agm-ms-asistencias python manage.py cerrar_sesiones_expiradas
```

Pulido y pruebas: [`docs/RESUMEN_CAMBIOS.md`](../docs/RESUMEN_CAMBIOS.md).  
Postman: carpeta **MS-5 Asistencias** en `docs/postman/AGM_API_Collection.json`.
