# MS-2 — Periodos & Materias

Catálogo académico: periodos lectivos (un solo activo a la vez), materias por periodo e importación desde PDF. Expone **gRPC** para MS-3, MS-4, MS-6 y MS-7.

## Puertos

| Protocolo | Puerto |
|-----------|--------|
| REST (Gunicorn) | **8002** |
| gRPC | **50052** |

Gateway: `http://localhost:8080/periodos/*` y `/materias/*` (nginx reescribe a `/api/periodos/`, `/api/materias/`).

## Variables de entorno

Ver `.env.example`. Críticas:

| Variable | Uso |
|----------|-----|
| `DB_*` | MySQL `agm_periodos_db` |
| `MS_AUTH_GRPC_*` | `ValidateToken` / roles vía MS-1 |
| `MS_ALUMNOS_GRPC_*` | Resolución docente (import PDF, futuro DELETE materia) |
| `GRPC_PORT` | Servidor `PeriodosService` |

## Endpoints REST

| Método | Ruta | Auth |
|--------|------|------|
| GET | `/api/periodos/` | JWT cualquier rol |
| POST | `/api/periodos/` | Admin |
| GET/PUT/DELETE | `/api/periodos/:id/` | JWT / Admin escritura |
| POST | `/api/periodos/:id/activar/` | Admin |
| GET | `/api/periodos/activo/` | **Público** (sin Bearer) |
| POST | `/api/periodos/:id/importar-materias/` | Admin (multipart `archivo`) |
| GET/POST | `/api/materias/` | JWT / Admin POST |
| GET/PUT/DELETE | `/api/materias/:id/` | JWT / Admin escritura |

Respuestas: envelope `{ success, data, message, errors? }` con paginación AGM en listados.

## Reglas de negocio

- Solo **un** periodo con `activo=True` (transacción + `select_for_update` en activar).
- No eliminar periodo con materias asociadas.
- `docente_id` en materia = **`usuario_id` de MS-1** (no PK de tabla Docente en MS-3).
- Import PDF: upsert por NRC; respuesta con contadores `importadas` / `fallidas`.

## gRPC (`periodos.proto`)

| RPC | Uso |
|-----|-----|
| `GetPeriodoActivo` | Periodo vigente |
| `GetMateriaById` | Detalle materia |
| `GetMateriasByDocente` | Listado por `docente_id` (usuario MS-1) |

Arranque: `python manage.py grpc_server` (incluido en `entrypoint.sh` del contenedor).

## Desarrollo

```bash
docker compose up -d ms-periodos db-periodos ms-auth
docker exec agm-ms-periodos python manage.py test apps.core.tests
./generate_proto.sh   # tras cambiar proto/
```

## Pruebas

Pulido y casos T1–T13: [`docs/RESUMEN_CAMBIOS.md`](../docs/RESUMEN_CAMBIOS.md).  
Postman: carpeta **MS-2 Periodos** en `docs/postman/AGM_API_Collection.json` (gateway + `{{jwt_token}}`).
