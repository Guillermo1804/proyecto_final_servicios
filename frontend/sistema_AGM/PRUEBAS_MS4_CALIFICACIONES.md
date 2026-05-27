# Pruebas frontend — MS-4 Calificaciones & Ponderaciones

## Requisitos previos

```bash
docker compose up -d rabbitmq db-auth ms-auth ms-auth-event-consumer \
  db-periodos ms-periodos db-alumnos ms-alumnos ms-alumnos-outbox-worker \
  db-calificaciones ms-calificaciones ms-calificaciones-worker-consumer \
  ms-calificaciones-worker-outbox nginx
```

**Importante:** MS-4 necesita proyecciones de materias y alumnos (consumer de eventos). Si el concentrado sale vacío, reinicia `ms-calificaciones-worker-consumer` y verifica inscripciones en MS-3.

Frontend:

```bash
cd frontend/sistema_AGM
npm start
```

Login como **docente** con `usuario_id` en tabla `docentes` y al menos una materia en MS-2 con su nombre.

Gateway: **http://127.0.0.1:8080**

---

## Docente — Detalle de materia (`/docente/materias/{nrc}`)

Ruta ejemplo: `/docente/materias/14502`

| # | Prueba | Esperado |
|---|--------|----------|
| 1 | Tab **Alumnos** | Sigue en MS-3 (`GET /alumnos/por-materia/`) |
| 2 | Tab **Evaluación** — cargar | `GET /ponderaciones/{materia_id}` (lista vacía o rubros guardados) |
| 3 | Crear rubros que sumen 100% y **Guardar plan** | `POST /ponderaciones/{materia_id}` con `{ ponderaciones: [{ nombre_categoria, porcentaje }] }` |
| 4 | Importar plan Excel | Columnas: `nombre_categoria` (o `categoria`/`nombre`) y `porcentaje` (o `peso`) → `POST /ponderaciones/{id}/importar` |
| 5 | Tab **Actividades** — crear actividad | Tras guardar plan: `POST /actividades/` con `ponderacion_id`, `nombre`, `descripcion`, `fecha` |
| 6 | Capturar calificación (0–10) | Al salir del input (blur): `POST /calificaciones/` con `actividad_id`, `alumno_id`, `calificacion` |
| 7 | Importar calificaciones Excel | Columnas: `matricula` (o `alumno_id`), `actividad_id`, `calificacion` → `POST /calificaciones/importar/{materia_id}` |
| 8 | Ver concentrado en tab Evaluación | `GET /concentrado/{materia_id}` — promedios reales y redondeados del backend |
| 9 | **Imprimir lista** | `POST /materias/{materia_id}/imprimir-lista` → ventana de impresión; inputs de nota quedan deshabilitados |
| 10 | **Cerrar materia** | `POST /materias/{materia_id}/cerrar` (MS-4, no solo cambio de estado en MS-2) |

**Escala de calificaciones en UI:** 0 a **10** (igual que el API).

---

## Endpoints MS-4 usados desde el front

| Acción | Método | URL |
|--------|--------|-----|
| Obtener/guardar ponderaciones | GET / POST | `/ponderaciones/{materia_id}` |
| Importar ponderaciones | POST | `/ponderaciones/{materia_id}/importar` |
| Listar actividades | GET | `/actividades/?materia={id}` |
| Crear actividad | POST | `/actividades/` |
| Guardar calificación | POST | `/calificaciones/` |
| Importar calificaciones | POST | `/calificaciones/importar/{materia_id}` |
| Concentrado | GET | `/concentrado/{materia_id}` |
| Cerrar materia | POST | `/materias/{materia_id}/cerrar` |
| Marcar lista impresa | POST | `/materias/{materia_id}/imprimir-lista` |

---

## Problemas comunes

| Síntoma | Solución |
|---------|----------|
| 401 | Iniciar sesión; token en sessionStorage |
| 403 al guardar | El docente logueado debe ser dueño de la materia (`docente_id` en proyección MS-4) |
| No se crea actividad | Primero guardar plan de evaluación (rubros con `ponderacion_id`) |
| 400 al calificar | Alumno inscrito en MS-3; nota entre 0 y 10 |
| 409 al editar | Lista ya impresa (`imprimir-lista`) |
| Concentrado vacío | Consumer MS-4 activo + inscripciones en MS-3 |

---

## Archivos frontend (MS-4)

- `src/app/models/calificaciones-api.model.ts`
- `src/app/services/docente-services/calificaciones.service.ts`
- `src/app/services/docente-services/detalle-materia-docente.service.ts`
- `src/app/screens/docente-screen/detalle-materia-screen/*`
- `proxy.conf.json` (prefijo `/concentrado`)

**Alumno `/alumno/notas`:** `GET /alumnos/me/materias/` + `GET /concentrado/{materia_id}` (MS-3 + MS-4).
