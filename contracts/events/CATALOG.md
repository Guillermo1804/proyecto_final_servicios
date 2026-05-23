# Catalogo de eventos AGM

## Exchange principal

| Propiedad | Valor |
|-----------|--------|
| Nombre | `agm.domain` |
| Tipo | `topic` |
| Durable | `true` |
| Auto-delete | `false` |

Los productores publican con **routing key** = `event_name`.

## Politicas de colas

### Cola de servicio

- Nombre: `ms-{servicio}.events` (ej. `ms-notificaciones.events`)
- Durable: `true`
- Bindings: routing keys que el microservicio consume (wildcards permitidos, ej. `alumno.*`)

### Cola de reintento

- Nombre: `ms-{servicio}.events.retry`
- Argumentos: `x-message-ttl` (ej. 30000 ms), `x-dead-letter-exchange` = `agm.domain`, `x-dead-letter-routing-key` = routing key original
- Proposito: backoff antes de reintentar consumo

### Dead Letter Queue (DLQ)

- Nombre: `ms-{servicio}.events.dlq`
- Mensajes: fallos tras `EVENT_CONSUME_MAX_RETRIES` o errores de esquema no recuperables
- Operacion: reproceso manual documentado en runbook (Fase 9)

## Eventos registrados

| event_name | version | aggregate_type | Productor | Consumidores | Schema payload |
|------------|---------|----------------|-----------|--------------|----------------|
| `health.ping.v1` | 1 | `health` | smoke test / ops | smoke test | `health.ping.v1.schema.json` |
| `user.created.v1` | 1 | `user` | **MS-1** | MS-3, **MS-4** | `user.created.v1.schema.json` |
| `user.updated.v1` | 1 | `user` | **MS-1** | **MS-4**, MS-6 | `user.updated.v1.schema.json` |
| `user.deactivated.v1` | 1 | `user` | **MS-1** | MS-4, MS-5, MS-6 (futuro) | `user.deactivated.v1.schema.json` |
| `user.role_changed.v1` | 1 | `user` | **MS-1** | MS-4, MS-5 (futuro) | `user.role_changed.v1.schema.json` |
| `token.revoked.v1` | 1 | `token` | **MS-1** | MS-2…MS-7 (futuro, cache) | `token.revoked.v1.schema.json` |
| `user.create_requested.v1` | 1 | `user` | **MS-3** | **MS-1** | `user.create_requested.v1.schema.json` |
| `alumno.imported.v1` | 1 | `alumno` | **MS-3** | MS-4, **MS-5**, MS-6, **MS-7** | `alumno.imported.v1.schema.json` |
| `alumno.updated.v1` | 1 | `alumno` | **MS-3** | MS-4, **MS-5**, MS-6, **MS-7** | `alumno.updated.v1.schema.json` |
| `alumno.withdrawn.v1` | 1 | `alumno` | **MS-3** | MS-4, **MS-5**, MS-6, **MS-7** | `alumno.withdrawn.v1.schema.json` |
| `docente.imported.v1` | 1 | `docente` | **MS-3** | MS-6 (Fase 5) | `docente.imported.v1.schema.json` |
| `password.reset_requested.v1` | 1 | `password` | MS-1 (futuro) | **MS-6** | `password.reset_requested.v1.schema.json` |
| `periodo.created.v1` | 1 | `periodo` | **MS-2** | **MS-4**, MS-5, **MS-7** | `periodo.created.v1.schema.json` |
| `periodo.updated.v1` | 1 | `periodo` | **MS-2** | **MS-4**, **MS-7** | `periodo.updated.v1.schema.json` |
| `periodo.activated.v1` | 1 | `periodo` | **MS-2** | MS-4, MS-5, **MS-7** | `periodo.activated.v1.schema.json` |
| `periodo.closed.v1` | 1 | `periodo` | **MS-2** | **MS-4**, **MS-5**, **MS-7** | `periodo.closed.v1.schema.json` |
| `materia.created.v1` | 1 | `materia` | **MS-2** | **MS-4**, **MS-5**, **MS-7** | `materia.created.v1.schema.json` |
| `materia.updated.v1` | 1 | `materia` | **MS-2** | **MS-4**, **MS-5**, **MS-7** | `materia.updated.v1.schema.json` |
| `materia.assigned_teacher.v1` | 1 | `materia` | **MS-2** | MS-4, MS-6, **MS-7** | `materia.assigned_teacher.v1.schema.json` |
| `materia.closed.v1` | 1 | `materia` | **MS-2** | **MS-4**, **MS-5**, MS-6, **MS-7** | `materia.closed.v1.schema.json` |
| `actividad.created.v1` | 1 | `actividad` | **MS-4** | **MS-7** | `actividad.created.v1.schema.json` |
| `calificacion.updated.v1` | 1 | `calificacion` | **MS-4** | **MS-7** | `calificacion.updated.v1.schema.json` |
| `concentrado.calculado.v1` | 1 | `concentrado` | **MS-4** | **MS-7** | `concentrado.calculado.v1.schema.json` |
| `materia.calificaciones_cerradas.v1` | 1 | `materia` | **MS-4** | **MS-6**, **MS-7** | `materia.calificaciones_cerradas.v1.schema.json` |
| `asistencia.registered.v1` | 1 | `asistencia` | **MS-5** | **MS-7** | `asistencia.registered.v1.schema.json` |
| `asistencia.rejected.v1` | 1 | `asistencia` | **MS-5** | **MS-7** | `asistencia.rejected.v1.schema.json` |
| `qr.session.created.v1` | 1 | `qr_session` | **MS-5** | **MS-7** | `qr.session.created.v1.schema.json` |

### health.ping.v1

- **Proposito:** prueba de humo del bus (Fase 1).
- **Routing key:** `health.ping.v1`
- **Payload:** `{ "message": "string" }`
