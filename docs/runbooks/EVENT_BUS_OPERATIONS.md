# Runbook — Operacion del bus de eventos AGM

Manual operativo para RabbitMQ, outbox, inbox, DLQ y recuperacion.

---

## 1. Topologia

| Componente | Valor |
|------------|--------|
| Exchange | `agm.domain` (topic, durable) |
| Vhost | `agm` (usuario `agm_bus`) |
| Routing key | Igual a `event_name` (ej. `alumno.imported.v1`) |

### Colas por microservicio

| Patron | Ejemplo | Uso |
|--------|---------|-----|
| Cola principal | `ms-{servicio}.events` | Consumo normal |
| Retry | `ms-{servicio}.events.retry` | TTL 30s, DLX de vuelta a cola principal |
| DLQ | `ms-{servicio}.events.dlq` | Fallos tras max reintentos o error de esquema |

### Workers en docker compose

| Worker | MS | Modo |
|--------|-----|------|
| ms-auth-outbox-worker | MS-1 | outbox relay |
| ms-auth-event-consumer | MS-1 | consume `user.create_requested.v1` |
| ms-periodos-outbox-worker | MS-2 | outbox |
| ms-alumnos-outbox-worker | MS-3 | outbox |
| ms-calificaciones-worker-outbox | MS-4 | outbox |
| ms-calificaciones-worker-consumer | MS-4 | proyecciones upstream |
| ms-asistencias-worker-outbox | MS-5 | outbox |
| ms-asistencias-worker-consumer | MS-5 | proyecciones upstream |
| ms-notificaciones-worker-consumer | MS-6 | correos async |
| ms-reportes-worker-consumer | MS-7 | proyecciones analiticas |

---

## 2. Variables de entorno

Definidas en `.env.example` (raiz) y replicadas en cada `ms-*/.env`:

```
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=agm_bus
RABBITMQ_PASSWORD=...
RABBITMQ_VHOST=agm
EVENT_EXCHANGE=agm.domain
EVENT_CONSUME_MAX_RETRIES=3
USE_EVENT_BUS=true
EVENT_CONTRACTS_DIR=/contracts/events
```

---

## 3. Flujo outbox (productores — R8)

1. Transaccion de negocio en Django.
2. `enqueue_domain_event(...)` inserta fila en `event_outbox` en la misma transaccion.
3. Tras `commit`, el worker `run_event_outbox` (o `AGM_RUN_MODE=outbox-worker`) publica a RabbitMQ.
4. Marca fila como publicada o reintenta si el broker no esta disponible.

**Verificacion:**

```bash
docker compose exec ms-periodos python manage.py shell -c \
  "from apps.core.models import EventOutbox; print(EventOutbox.objects.filter(published_at__isnull=True).count())"
```

---

## 4. Flujo inbox (consumidores — R7)

1. Worker `run_event_consumer` hace `basic_get` de `ms-{servicio}.events`.
2. Valida envelope + JSON Schema (`agm_events.validation`).
3. `try_register_event(event_id)` en `event_inbox`; si duplicado, ACK sin reprocesar.
4. Ejecuta handler de dominio (proyeccion, correo, etc.).
5. ACK del mensaje.

**Duplicados:** mismo `event_id` dos veces debe dejar una sola fila en `event_inbox` y un solo efecto de negocio.

---

## 5. Dead Letter Queue (DLQ)

### Cuando un mensaje va a DLQ

- Error de validacion de esquema no recuperable.
- Excepcion en handler tras `EVENT_CONSUME_MAX_RETRIES` reintentos (via cola `.retry`).

### Inspeccion

Consola RabbitMQ: http://localhost:15672 (credenciales del compose).

```bash
docker compose exec rabbitmq rabbitmqctl list_queues name messages -p agm
```

### Reproceso manual (replay)

1. Identificar mensaje en `ms-{servicio}.events.dlq` (conservar JSON completo del envelope).
2. Corregir causa raiz (bug, schema, datos).
3. Republicar a exchange con routing key original:

```python
# Desde contenedor con agm_events instalado
from agm_events.config import EventBusConfig
from agm_events.publisher import EventPublisher
# body = bytes del mensaje DLQ
# publisher.publish(envelope)  # o basic_publish manual
```

4. Si el `event_id` ya esta en `event_inbox`, eliminar esa fila **solo** tras autorizacion operativa y conocimiento del efecto (reproceso con nuevo `event_id` es mas seguro para side effects).

---

## 6. Monitoreo de lag

Indicadores:

| Metrica | Como medirla |
|---------|----------------|
| Profundidad de cola | `rabbitmqctl list_queues` campo `messages` |
| Outbox pendiente | `COUNT(*) FROM event_outbox WHERE published_at IS NULL` por MS |
| `data_as_of` MS-7 | Campo en respuestas de reportes / tabla `report_analytics_state` |
| Historial correo MS-6 | Tabla `historial_correo`, columna `estado_envio` |

Alertas sugeridas (produccion):

- Cola principal > 100 mensajes por 5 minutos.
- Outbox pendiente > 0 por mas de 2 minutos con broker sano.
- DLQ con mensajes nuevos.

---

## 7. Smoke test

```bash
docker compose up -d rabbitmq
python packages/agm_events/smoke_test.py
```

Publica `health.ping.v1` y valida consumo + inbox.

---

## 8. Contactos y escalamiento

1. Revisar logs del worker consumidor (`docker compose logs -f ms-reportes-worker-consumer`).
2. Consultar `contracts/events/CATALOG.md` para schema esperado.
3. Escalar a equipo de desarrollo si falla validacion de contrato o migracion pendiente.
