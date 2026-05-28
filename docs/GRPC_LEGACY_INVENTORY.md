# Inventario gRPC legacy (Fase 9)

Modulos de cliente gRPC de negocio marcados con `block_business_grpc` cuando `USE_EVENT_BUS=true`.

## MS-2 Periodos

| Modulo | Funciones bloqueadas |
|--------|---------------------|
| `grpc_clients/auth_client.py` | `get_auth_stub`, `validate_token` (legacy) |

Hot path REST: JWT local (`utils/jwt_local.py`).

## MS-3 Alumnos

| Modulo | Funciones bloqueadas |
|--------|---------------------|
| `grpc_clients/auth_client.py` | creacion usuario sync |
| `grpc_clients/periodos_client.py` | consultas materia |
| `utils/auth_client.py` | `create_user_alumno` |
| `utils/notificaciones_client.py` | `send_bienvenida`, `send_baja_notif` |
| `utils/periodos_client.py` | `get_materia_docente_id` |

Hot path: outbox `alumno.*`, `user.create_requested.v1`, proyeccion materia local.

## MS-4 Calificaciones

| Modulo | Funciones bloqueadas |
|--------|---------------------|
| `grpc_clients/__init__.py` | `validate_token`, `get_alumno_by_id`, `get_materia_by_id`, etc. |
| `utils/notificaciones_client.py` | `send_cierre_materia` |

Hot path: JWT local, proyecciones, `materia.calificaciones_cerradas.v1`.

## MS-5 Asistencias

| Modulo | Funciones bloqueadas |
|--------|---------------------|
| `grpc_clients.py` | `validate_token`, `get_alumno_by_id`, `is_alumno_en_materia` |

Hot path: JWT local, proyecciones periodo/materia/alumno, eventos asistencia.

## MS-6 Notificaciones

| Modulo | Funciones bloqueadas |
|--------|---------------------|
| `grpc_clients/*` | consultas a MS-2/MS-3 |
| `services/data_provider.py` | clase `GrpcDataProvider` |

Hot path: `EmailPayloadService` + eventos en `event_bus/consumers.py`.

Admin REST: `X-Internal-Api-Key` o JWT via `utils/jwt_local.py`.

## MS-7 Reportes

| Modulo | Estado |
|--------|--------|
| `grpc_clients/*_client.py` | Bloqueados; no usados en `report_data_service` |
| `apps/reportes/exceptions.py` | Excepciones de dominio (sin gRPC) |

Hot path: proyecciones `reporte_*_projection`, `data_as_of`.

## MS-1 Auth

| Modulo | Estado |
|--------|--------|
| `apps/core/grpc_clients.py` | DEPRECATED; sustituido por `password.reset_requested.v1` con bus activo |

Servidor gRPC MS-1: soporte legacy `ValidateToken` (no usado por otros MS con bus activo).
