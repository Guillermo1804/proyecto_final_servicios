# AGM Postman Collection

Colección y entorno para probar APIs de los microservicios AGM.

## Archivos

| Archivo | Contenido |
|---------|-----------|
| `AGM_API_Collection.json` | MS-2 Periodos, MS-3 Alumnos, MS-6 Notificaciones, **MS-7 Reportes** |
| `AGM_Environment.json` | URLs locales, `internal_api_key`, `jwt_token`, IDs MS-7 |

También: [`../postman_collection.json`](../postman_collection.json) (auth + gateway).

## Importación

1. Postman → **Import** → ambos JSON de esta carpeta.
2. Seleccionar environment **AGM Local Environment**.

## Variables

| Variable | Default | Uso |
|----------|---------|-----|
| `base_url_periodos` | `http://localhost:8002` | MS-2 directo |
| `base_url_alumnos` | `http://localhost:8003` | MS-3 directo |
| `base_url_notificaciones` | `http://localhost:8006` | MS-6 health directo |
| `base_url_gateway` | `http://localhost:8080` | MS-6 REST (recomendado) |
| `internal_api_key` | placeholder | Debe coincidir con `INTERNAL_API_KEY` en `ms-notificaciones/.env` |

## MS-6 Notificaciones (Epic 8)

Todos los POST usan header **`X-Internal-Api-Key: {{internal_api_key}}`**.

| Request | Ruta gateway |
|---------|----------------|
| Bienvenida | `POST /notificaciones/bienvenida` |
| Baja | `POST /notificaciones/baja` |
| Cierre materia | `POST /notificaciones/cierre-materia` |
| Reset password | `POST /notificaciones/reset-password` |

Documentación: [`../../ms-notificaciones/README.md`](../../ms-notificaciones/README.md).

## MS-7 Reportes y Estadísticas (Epic 9)

Obtener JWT: `POST {{base_url_gateway}}/auth/login` → copiar `access_token` a `jwt_token`.

| Request | Ruta gateway |
|---------|----------------|
| Calificaciones Excel | `GET /reportes/calificaciones/{{materia_id}}?formato=xlsx` |
| Calificaciones PDF | `GET /reportes/calificaciones/{{materia_id}}?formato=pdf` |
| Asistencias Excel | `GET /reportes/asistencias/{{materia_id}}?formato=xlsx` |
| Asistencias PDF | `GET /reportes/asistencias/{{materia_id}}?formato=pdf` |
| Stats docente | `GET /estadisticas/docente/{{docente_usuario_id}}` |
| Stats alumno | `GET /estadisticas/alumno/{{alumno_id}}` |

Header: **`Authorization: Bearer {{jwt_token}}`**. `internal_api_key` solo aplica a MS-6.

Documentación: [`../../ms-reportes/README.md`](../../ms-reportes/README.md).
