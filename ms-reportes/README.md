# MS-7 — Reportes y Estadísticas

Microservicio Django que agrega datos vía **gRPC** (MS-1…MS-5), genera reportes **Excel/PDF** y expone estadísticas **JSON** con envelope AGM. No accede a bases de datos de otros MS.

## Puertos oficiales

| Protocolo | Puerto | Uso |
|-----------|--------|-----|
| REST (Gunicorn) | **8007** | Reportes binarios + estadísticas JSON + `/health/` |
| gRPC | **50057** | `GenerateReport`, `GetHistorialDocente` (`reportes.proto`) |

**Gateway Nginx:** `http://localhost:8080/reportes/*` y `/estadisticas/*` → MS-7:8007.

## Variables de entorno críticas

Copiar `.env.example` → `.env`. Valores sensibles **no** deben commitearse.

| Variable | Descripción |
|----------|-------------|
| `REST_PORT` | Puerto HTTP (default `8007`) |
| `GRPC_PORT` | Puerto gRPC servidor (default `50057`) |
| `DB_*` | MySQL `agm_reportes_db` (solo metadatos/caché opcional) |
| `MS_*_GRPC_HOST` / `MS_*_GRPC_PORT` | Upstreams MS-1…MS-5 |
| `GRPC_CLIENT_TIMEOUT` | Timeout general clientes gRPC (s) |
| `GRPC_CLIENT_TIMEOUT_CALIFICACIONES` | Timeout `GetConcentrado` (s, default 30) |
| `USE_MOCK_DATA` | **`False`** en Docker/producción; `True` solo tests unitarios aislados |
| `ESTADISTICAS_DOCENTE_MAX_MATERIAS` | Límite materias en historial docente |
| `STATS_ALUMNO_MATERIA_IDS` | IDs de materia para stats alumno en dev |

## Convención de identificadores (plan §5.4)

| Parámetro | Significado | Fuente |
|-----------|-------------|--------|
| `materiaId` en `/reportes/.../<id>` | PK materia en **MS-2** | `GetMateriaById` |
| `id` en `/estadisticas/docente/<id>` | **`usuario_id` de MS-1** (titular en `Materia.docente_id`) | No usar PK `Docente.id` de MS-3 |
| `id` en `/estadisticas/alumno/<id>` | PK **`Alumno.id` en MS-3** | gRPC alumnos |

Confundir `Docente.id` (MS-3) con `usuario_id` (MS-1) provoca **403** en reportes.

## API REST

### Reportes (respuesta binaria)

| Método | Ruta | Query |
|--------|------|-------|
| GET | `/reportes/calificaciones/<materiaId>` | `formato=xlsx` \| `xls` \| `pdf` |
| GET | `/reportes/asistencias/<materiaId>` | `formato=xlsx` \| `xls` \| `pdf` |

- Header: `Authorization: Bearer <JWT>` (validado vía MS-1 `ValidateToken`).
- RBAC: docente titular de la materia o `admin`.
- Errores: envelope JSON (400, 401, 403, 404, 503).

### Estadísticas (JSON envelope)

| Método | Ruta |
|--------|------|
| GET | `/estadisticas/docente/<usuario_id>` |
| GET | `/estadisticas/alumno/<alumno_id>` |

## gRPC servidor (`:50057`)

| RPC | Equivalente REST |
|-----|------------------|
| `GenerateReport` | `GET /reportes/{tipo}/:materiaId` |
| `GetHistorialDocente` | `GET /estadisticas/docente/:id` |

Generar stubs: `./generate_proto.sh` (desde `../proto`).

## Desarrollo local

```bash
docker compose up -d ms-reportes db-reportes
docker exec agm-ms-reportes python manage.py test apps.reportes.tests
curl http://localhost:8007/health/
```

## Postman

Carpeta **MS-7** en `docs/postman/AGM_API_Collection.json`. Variables: `base_url_gateway`, `jwt_token`, `materia_id`, `docente_usuario_id`, `alumno_id`.

## Pruebas

Pulido y casos R1–R10: [`docs/RESUMEN_CAMBIOS.md`](../docs/RESUMEN_CAMBIOS.md).
