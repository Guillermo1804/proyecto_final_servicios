# Consistencia de datos entre microservicios (proyecciones)

## Modelo actual (sin romper arquitectura)

Cada MS conserva **su propia BD**. Los MS consumidores (3, 4, 5, 7) mantienen **read models locales** actualizados por:

1. **Bus de eventos** (vía principal): outbox → RabbitMQ → inbox → handler.
2. **Reconciliación** (red de seguridad): comando idempotente que lee las BD fuente (MS-2 / MS-3) y hace upsert.

No se elimina gRPC ni REST. No se unifican bases de datos. Se **suma** una red de seguridad operativa.

```
MS-2 (periodos/materias) ──eventos──► MS-4 / MS-5 / MS-7
         │                                    ▲
         └──────── BACKFILL_* (lectura) ───────┘  ← reconcile_projections
MS-3 (alumnos) ──eventos──► MS-4 / MS-5 / MS-7
         │
         └──────── sync / BACKFILL_* ───────────► reconcile
```

## Por qué puede haber “drift”

| Causa | Ejemplo |
|-------|---------|
| Handler faltante | `periodo.activated.v1` no actualizaba `periodo_activo` en MS-5 |
| Consumer caído | Worker no corriendo tras `docker compose up` |
| Reset parcial de BD | Solo MS-1…4 reiniciados; proyecciones MS-5 quedaron viejas |
| Evento único sin `updated` | MS-2 emite solo `periodo.activated.v1` al activar (no `periodo.updated.v1`) |

El bus sigue siendo la fuente **en tiempo real**; la reconciliación corrige el estado **eventual** cuando algo se perdió.

## Herramientas (aditivas)

### 1. Registro de contratos

`contracts/events/consumer_bindings.json` — lista de `event_name` que cada MS **debe** tener en `HANDLERS`.

Tests (`agm_events.consumer_bindings`) fallan en CI si falta un handler (evita repetir el bug de `periodo.activated`).

### 2. Comandos por servicio

| MS | Comando | Qué hace |
|----|---------|----------|
| MS-3 | `python manage.py reconcile_projections` | Llama a `sync_materia_projections` (MS-2 → materia_projection) |
| MS-4 | `python manage.py reconcile_projections` | `backfill_calificaciones_projections` |
| MS-5 | `python manage.py reconcile_projections` | `backfill_asistencias_projections` |

Requisitos en `.env` (ya documentados en cada MS): `BACKFILL_PERIODOS_DB_*`, `BACKFILL_ALUMNOS_DB_*`.

### 3. Script único

```bash
./scripts/reconcile-projections.sh
# o en Windows:
./scripts/reconcile-projections.ps1
```

Ejecutar después de:

- Reset de volúmenes MySQL
- Import masivo de alumnos / programación
- Activar o cerrar periodos en Admin
- Sospecha de datos desalineados en QR, calificaciones o listas

### 4. Operación normal

- Workers `*-worker-consumer` y `*-outbox-worker` deben estar **Up**.
- Tras cambios en `consumers.py`, reiniciar el consumer del MS afectado.

## Checklist rápido

1. `docker compose ps` → consumers y outbox en ejecución.
2. Activar periodo en MS-2 (Admin) → verificar que MS-5 refleja `periodo_activo=True` en proyección.
3. Si no: `docker compose exec ms-asistencias python manage.py reconcile_projections`.
4. Tests de bindings: `docker compose exec ms-asistencias python manage.py test apps.core.tests.test_consumer_bindings`.

## MS-7 (reportes)

`rebuild_report_projections --from-backfill` **trunca** tablas analíticas; usar solo en mantenimiento o demo, no en el script estándar de reconciliación.

## Referencias

- `contracts/events/CATALOG.md`
- `contracts/events/consumer_bindings.json`
- `docs/runbooks/EVENT_BUS_OPERATIONS.md`
