# Contratos de eventos AGM

## Convenciones

- **Routing key** = `event_name` (ej. `health.ping.v1`, `alumno.importado.v1`).
- **Exchange** = `agm.domain` (tipo `topic`, durable).
- Cada evento tiene un archivo `{event_name}.schema.json` para el `payload`.
- El sobre del mensaje se valida con `_envelope.schema.json`.

## Estructura del sobre

Ver `_envelope.schema.json`. Campos obligatorios: `event_id`, `event_name`, `event_version`, `aggregate_type`, `aggregate_id`, `source_service`, `correlation_id`, `causation_id`, `occurred_at`, `payload`.

## Colas por consumidor

Patron: `ms-{servicio}.events` con bindings por routing keys que el MS consume.

## Reintento y DLQ

Por cada cola principal `ms-{x}.events`:

1. **Retry:** `ms-{x}.events.retry` — mensaje con TTL; al expirar, dead-letter de vuelta a la cola principal.
2. **DLQ:** `ms-{x}.events.dlq` — mensajes que superan `EVENT_CONSUME_MAX_RETRIES` o errores no recuperables.

Detalle en `CATALOG.md`.
