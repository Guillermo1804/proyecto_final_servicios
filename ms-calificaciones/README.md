# MS-4 — Calificaciones & Ponderaciones

Ponderaciones por materia (suma 100 %), actividades, registro e importación de calificaciones, concentrado con promedios institucionales y **gRPC** para MS-7.

## Puertos

| Protocolo | Puerto |
|-----------|--------|
| REST | **8004** |
| gRPC | **50054** |

Gateway: `/ponderaciones/`, `/actividades/`, `/calificaciones/`, `/concentrado/`, `/materias/:id/cerrar`, `/materias/:id/imprimir-lista`.

## Variables de entorno

Ver `.env.example`. Clientes gRPC: MS-1 (auth), MS-2 (materia/docente), MS-3 (alumnos), MS-6 (cierre).

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST/PUT | `/ponderaciones/:materia_id` | CRUD ponderaciones |
| POST | `/ponderaciones/:materia_id/importar` | Excel categorías |
| GET/POST | `/actividades?materia=` | Listar / crear actividades |
| POST | `/calificaciones` | Upsert calificación |
| POST | `/calificaciones/importar/:materia_id` | Import Excel |
| GET | `/concentrado/:materia_id` | Tabla alumnos + promedios |
| POST | `/materias/:id/cerrar` | Cierre + notificación |
| POST | `/materias/:id/imprimir-lista` | Bloquea edición |

Solo el **docente titular** (o admin) gestiona una materia (`docente_id` = `user_id` MS-1).

## Desarrollo

```bash
docker compose up -d ms-calificaciones db-calificaciones ms-auth ms-periodos ms-alumnos
docker exec agm-ms-calificaciones python manage.py test apps.core.tests
```

Pulido y pruebas: [`docs/RESUMEN_CAMBIOS.md`](../docs/RESUMEN_CAMBIOS.md).  
Postman: carpeta **MS-4 Calificaciones** en `docs/postman/AGM_API_Collection.json`.
