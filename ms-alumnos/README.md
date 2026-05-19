# MS-3 — Docentes & Alumnos

Gestión de docentes, alumnos, inscripciones por materia, importaciones (PDF docentes, CSV/Excel alumnos) y **gRPC** para MS-4, MS-5 y MS-7.

## Puertos

| Protocolo | Puerto |
|-----------|--------|
| REST | **8003** |
| gRPC | **50053** |

Gateway: `http://localhost:8080/docentes/*` y `/alumnos/*`.

## Variables de entorno

Ver `.env.example`. Críticas: `DB_*`, `MS_AUTH_GRPC_*`, `MS_PERIODOS_GRPC_*`, `MS_NOTIFICACIONES_GRPC_*`.

## Endpoints REST principales

| Método | Ruta | Auth |
|--------|------|------|
| GET/POST | `/api/docentes/` | JWT / Admin POST |
| POST | `/api/docentes/importar/` | Admin (multipart `file` PDF) |
| POST | `/api/alumnos/importar/preview/` | Admin (multipart `archivo`) |
| POST | `/api/alumnos/importar/confirmar/` | Admin (JSON `alumnos`, opcional `materia_id`) |
| GET | `/api/alumnos/por-materia/?materia_id=` | JWT |
| GET | `/api/alumnos/me/materias/` | Alumno |
| POST | `/api/alumnos/:id/baja-materia/` | JWT (body `materia_id`) |

## gRPC (`alumnos.proto`)

`GetAlumnosByMateria`, `GetAlumnoById`, `IsAlumnoEnMateria` en **50053**.

## Desarrollo

```bash
docker compose up -d ms-alumnos db-alumnos ms-auth ms-periodos
docker exec agm-ms-alumnos python manage.py test apps.core.tests
```

Pulido y pruebas: [`docs/RESUMEN_CAMBIOS.md`](../docs/RESUMEN_CAMBIOS.md).  
Postman: carpeta **MS-3 Alumnos** en `docs/postman/AGM_API_Collection.json`.
