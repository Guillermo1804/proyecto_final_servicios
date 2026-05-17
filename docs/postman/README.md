# AGM Postman Collection

Colección y entorno para probar APIs de los microservicios AGM.

## Archivos

| Archivo | Contenido |
|---------|-----------|
| `AGM_API_Collection.json` | MS-2 Periodos, MS-3 Alumnos, **MS-6 Notificaciones** |
| `AGM_Environment.json` | URLs locales y `internal_api_key` |

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
