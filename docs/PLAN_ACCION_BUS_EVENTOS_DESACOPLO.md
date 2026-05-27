# Plan de acción — Bus de eventos y desacoplo (trabajo por fases)

**Versión:** 3.0 — ejecución **tú + asistente (Cursor)**, un microservicio por fase de dominio.  
**Objetivo final:** los 7 MS operan de forma autónoma; la integración entre dominios es por **RabbitMQ** (eventos + outbox/inbox), sin gRPC en flujos de negocio.

---

## Cómo vamos a trabajar (obligatorio)

Este plan está pensado para que **lo implementes tú** con ayuda del asistente. Reglas de trabajo:

1. **Una fase a la vez.** No se empieza la fase N+1 hasta tu confirmación explícita (“continúa”, “aprobado”, etc.).
2. **Al terminar cada fase**, el asistente debe:
   - listar **archivos creados o modificados**;
   - resumir **qué quedó funcionando**;
   - indicar **cómo probar solo esa fase** (comandos `docker compose`, curls, tests);
   - mostrar el **checklist de la fase** marcado;
   - **preguntar:** *“¿Confirmas que la Fase X está OK para pasar a la Fase Y?”*
3. **Pruebas por microservicio:** en cada fase de MS solo levantamos lo necesario (ver “Compose mínimo” por fase) para no mezclar errores de otros servicios.
4. **Feature flag:** `USE_EVENT_BUS=true` por defecto en todo el monorepo (Fase 9). Solo `false` para rollback local documentado.

### Registro de avance (rellenar tú)

| Fase | Nombre | Estado | Fecha | Confirmado por ti |
|------|--------|--------|-------|-------------------|
| 1 | Infraestructura + librería común | ✅ Completada | 2026-05-22 | Sí |
| 2 | MS-1 Auth & Users | ✅ Completada | 2026-05-23 | Sí |
| 3 | MS-2 Periodos & Materias | ✅ Completada | 2026-05-23 | Sí |
| 4 | MS-3 Docentes & Alumnos | ✅ Completada | 2026-05-23 | Sí |
| 5 | MS-6 Notificaciones | ✅ Completada | 2026-05-23 | Sí |
| 6 | MS-4 Calificaciones | ✅ Completada | 2026-05-23 | Sí |
| 7 | MS-5 Asistencias QR | ✅ Completada | 2026-05-23 | Sí |
| 8 | MS-7 Reportes & Stats | ✅ Completada | 2026-05-23 | Sí |
| 9 | Cierre: retiro gRPC + docs + sistema completo | ✅ Completada | 2026-05-23 | Pendiente confirmación |

---

## Mapa rápido de fases

| Fase | Alcance (de → hasta) | Microservicio / ámbito |
|------|----------------------|-------------------------|
| **1** | Repo sin bus → bus operativo + librería + prueba humo | Transversal (sin lógica de negocio en 7 MS) |
| **2** | MS-1 acoplado por gRPC → MS-1 autónomo + JWKS + eventos identidad | **MS-1** |
| **3** | MS-2 con ValidateToken gRPC → JWT local + publica eventos periodo/materia | **MS-2** |
| **4** | MS-3 con gRPC a MS-1/MS-6 → publica eventos alumnos; sin gRPC a MS-6 | **MS-3** |
| **5** | MS-6 invocado por gRPC → MS-6 solo consume bus; correos async | **MS-6** (+ prueba integrada con MS-3) |
| **6** | MS-4 con gRPC MS-2/3/6 → proyecciones + eventos calificaciones | **MS-4** |
| **7** | MS-5 con gRPC MS-1/3 → proyecciones + eventos asistencia | **MS-5** |
| **8** | MS-7 agregador gRPC → proyecciones + reportes locales | **MS-7** |
| **9** | Sistema híbrido → gRPC de negocio retirado; docs al día; prueba E2E | Todo el monorepo |

**Orden MS-5 y MS-6:** MS-6 antes que MS-4 porque desacopla correos pronto (Fase 5) y valida el bus con un solo consumidor; MS-4 y MS-5 consumen eventos de MS-2/MS-3 ya publicados en fases 3–4.

---

# FASE 1 — Infraestructura y librería común

## Alcance

**Desde:** repositorio actual sin RabbitMQ ni `agm_events`.  
**Hasta:** RabbitMQ en Docker, carpeta de contratos, librería Python compartida, **prueba humo** publicar/consumir (puede ser script o MS mínimo temporal).

**No incluye:** cambiar lógica de negocio de MS-1…MS-7; JWT local; retirar gRPC.

## Compose mínimo para probar

```text
rabbitmq
db-auth (solo si el humo usa Django en ms-auth; alternativa: script Python en shared/)
```

Opcional: ningún MS REST; solo `rabbitmq` + comando `python -m agm_events.smoke_test`.

## Tareas (checklist)

- [ ] Servicio `rabbitmq` en `docker-compose.yml` (volumen, healthcheck, red `agm-network`).
- [ ] Variables documentadas en `.env.example` raíz y referencia en plan.
- [ ] Exchange `agm.domain` (topic), política de colas retry/DLQ documentada en `contracts/events/README.md`.
- [ ] Carpeta `contracts/events/` con `_envelope.schema.json` y `CATALOG.md` (vacío o con `health.ping.v1` solo).
- [ ] Paquete `packages/agm_events/` (o `shared/agm_events/`): envelope, publisher, consumer base, outbox/inbox helpers.
- [ ] Comando o test de humo: publica `health.ping.v1` → consumidor guarda en inbox (BD SQLite temporal o `db-auth` de prueba).
- [ ] Prueba duplicado: mismo `event_id` dos veces → un solo registro inbox.
- [ ] Prueba broker caído: outbox pendiente → al subir rabbit, se publica.

## Criterio de “fase terminada”

Puedes ejecutar humo local sin levantar los 7 microservicios.

## Al cerrar la fase — el asistente te muestra

1. Diff de `docker-compose.yml` y estructura `packages/agm_events/`, `contracts/events/`.
2. Salida del smoke test (logs con `event_id`, `correlation_id`).
3. Checklist anterior completado.

**Pregunta de confirmación:** *¿Confirmas Fase 1 OK para iniciar Fase 2 (MS-1 Auth)?*

---

# FASE 2 — MS-1 Auth & Users

## Alcance

**Desde:** MS-1 solo como servicio REST/gRPC actual.  
**Hasta:** MS-1 con **outbox**, publicación de eventos de identidad, endpoint **JWKS** (o clave pública), workers `run_event_outbox` / (si consume) `run_event_consumer` para `user.create_requested.v1`. MS-1 **no depende** de otros MS para operar login/registro.

**No incluye:** quitar `ValidateToken` en MS-2…MS-7 (eso va fase por fase en cada MS); MS-3 publicando alumnos.

## Compose mínimo para probar

```text
rabbitmq, db-auth, ms-auth
ms-auth-worker-outbox (o proceso en entrypoint)
```

## Tareas (checklist)

- [ ] Migración Django: tabla `event_outbox` (y `event_inbox` si MS-1 consume).
- [ ] Integrar `agm_events` en `ms-auth`.
- [ ] Publicar tras commit: `user.created.v1`, `user.updated.v1`, `user.deactivated.v1`, `user.role_changed.v1`, `token.revoked.v1` (según existan esos flujos en código).
- [ ] Endpoint JWKS o ruta documentada para clave pública JWT.
- [ ] Consumidor opcional: `user.create_requested.v1` → crea usuario → `user.created.v1`.
- [ ] `USE_EVENT_BUS=true` solo en `ms-auth` para eventos.
- [ ] Tests: registro/login con **solo** MS-1 + MySQL + Rabbit levantados.
- [ ] Test: parar Rabbit → crear usuario → outbox `pending` → levantar Rabbit → evento `published`.

## Prueba individual MS-1

| # | Acción | Resultado esperado |
|---|--------|-------------------|
| 1 | `POST /auth/login/` (o ruta existente) | 200 + JWT |
| 2 | Crear usuario | Fila en outbox → mensaje en cola Rabbit |
| 3 | `GET` JWKS | Clave usable para validar JWT offline |
| 4 | `docker stop` otros MS | Login sigue funcionando |

## Al cerrar la fase

1. Lista de eventos MS-1 en `contracts/events/CATALOG.md`.
2. Comandos exactos que usaste.
3. Captura o log de un evento en Rabbit Management (si UI habilitada).

**Pregunta:** *¿Confirmas Fase 2 OK para Fase 3 (MS-2)?*

---

# FASE 3 — MS-2 Periodos & Materias

## Alcance

**Desde:** MS-2 llama `ValidateToken` a MS-1 por gRPC en requests.  
**Hasta:** MS-2 valida **JWT localmente** (JWKS MS-1); publica eventos de periodo/materia con outbox; **no llama a ningún otro MS** en su CRUD principal.

**No incluye:** consumidores en MS-4/MS-7; MS-3.

## Compose mínimo

```text
rabbitmq, db-auth, ms-auth (solo JWKS; puede estar caído el gRPC si JWT ya en cache)
db-periodos, ms-periodos, ms-periodos-worker-outbox
```

## Tareas (checklist)

- [ ] Outbox/inbox en `ms-periodos`.
- [ ] Middleware/auth: JWT local; **eliminar** llamada gRPC `ValidateToken` en hot path.
- [ ] Publicar: `periodo.created.v1`, `periodo.updated.v1`, `periodo.activated.v1`, `periodo.closed.v1`, `materia.created.v1`, `materia.updated.v1`, `materia.assigned_teacher.v1`, `materia.closed.v1`.
- [ ] Schemas JSON en `contracts/events/` para cada evento publicado.
- [ ] `USE_EVENT_BUS=true` en ms-periodos.
- [ ] Tests REST de periodos/materias sin levantar MS-3…MS-7.

## Prueba individual MS-2

| # | Acción | Resultado esperado |
|---|--------|-------------------|
| 1 | Login en MS-1, llamar API MS-2 con JWT | 200 sin gRPC runtime a MS-1 |
| 2 | Crear/cerrar materia | Evento en Rabbit + outbox `published` |
| 3 | `docker stop ms-auth` (tras JWT emitido) | Endpoints MS-2 con token válido siguen OK |

## Al cerrar la fase

Entregables + checklist + comandos.

**Pregunta:** *¿Confirmas Fase 3 OK para Fase 4 (MS-3)?*

---

# FASE 4 — MS-3 Docentes & Alumnos

## Alcance

**Desde:** MS-3 llama MS-6 (`SendBienvenida`, `SendBajaNotif`) y MS-1 (crear usuario) de forma sincrónica.  
**Hasta:** MS-3 publica `alumno.imported.v1`, `alumno.updated.v1`, `alumno.withdrawn.v1`, `docente.imported.v1`, etc.; **payload completo** para correos; flujo usuario vía `user.create_requested.v1` (outbox); **sin gRPC a MS-6**.

**No incluye:** MS-6 consumiendo (Fase 5); read models en MS-4/MS-5.

## Compose mínimo

```text
rabbitmq, db-auth, ms-auth, db-alumnos, ms-alumnos, ms-alumnos-worker-outbox
```

(MS-1 necesario si pruebas creación usuario async; para solo importar alumno y ver evento, puede bastar outbox.)

## Tareas (checklist)

- [ ] Outbox en `ms-alumnos`.
- [ ] JWT local (igual que MS-2).
- [ ] Sustituir llamadas MS-6 por publicación de eventos (flag `USE_EVENT_BUS`).
- [ ] Tabla `pending_user_creation` + `user.create_requested.v1` hacia bus (MS-1 consumirá en Fase 2 si ya está; si no, dejar evento documentado).
- [ ] Payload mínimo `alumno.imported.v1`: ids, email, nombre, matricula, materia_id, docente_email, periodo_id.
- [ ] Importación: outbox por lotes si import masivo.
- [ ] Tests: importar alumno / baja **sin** levantar MS-6.

## Prueba individual MS-3

| # | Acción | Resultado esperado |
|---|--------|-------------------|
| 1 | Importar alumno (demo) | 200/202 API; outbox → Rabbit `alumno.imported.v1` |
| 2 | Baja alumno | Evento `alumno.withdrawn.v1`; **no** error si MS-6 apagado |
| 3 | Duplicar publicación mismo `event_id` | Un mensaje lógico (outbox idempotente) |

## Al cerrar la fase

Mostrar mensaje JSON de ejemplo en cola; CATALOG actualizado.

**Pregunta:** *¿Confirmas Fase 4 OK para Fase 5 (MS-6)?*

---

# FASE 5 — MS-6 Notificaciones

## Alcance

**Desde:** MS-6 expuesto por gRPC y llamado por MS-3/MS-4; consulta MS-2/MS-3 por datos.  
**Hasta:** MS-6 **solo consume** eventos; envía correo en worker interno; inbox + `HistorialCorreo` con `event_id`; **no gRPC entrante de negocio** desde MS-3/MS-4.

**Incluye prueba integrada:** MS-3 + MS-6 + Rabbit (primer flujo punta a punta de negocio).

**No incluye:** MS-4 cierre materia por evento (puede quedar para Fase 6 si MS-4 aún no publica).

## Compose mínimo

```text
rabbitmq, db-alumnos, ms-alumnos (+ worker outbox)
db-notificaciones, ms-notificaciones, ms-notificaciones-worker-consumer
db-auth, ms-auth (JWKS para API MS-6 si tiene REST protegido)
```

## Tareas (checklist)

- [ ] Cola `ms-notificaciones.events` + bindings `alumno.*`, `materia.closed.v1`, `password.reset_requested.v1`.
- [ ] Inbox + handlers: bienvenida, baja, reset password.
- [ ] Worker SMTP separado del ack del bus.
- [ ] Eliminar (o desactivar con flag) clientes gRPC desde MS-3 hacia MS-6.
- [ ] Retirar gRPC MS-6 → MS-2/MS-3 para plantillas (datos vienen en payload).
- [ ] DLQ + estados en historial: sent, failed, retrying, dead_letter.
- [ ] `USE_EVENT_BUS=true` en ms-alumnos y ms-notificaciones.

## Prueba MS-6 (+ MS-3)

| # | Acción | Resultado esperado |
|---|--------|-------------------|
| 1 | Importar alumno en MS-3 | Correo encolado/enviado en MS-6; historial con `event_id` |
| 2 | `docker stop ms-alumnos` y replay manual o mensaje en cola | MS-6 procesa sin llamar MS-3 |
| 3 | SMTP caído | Consumidor sigue; reintentos; API MS-3 no falló |
| 4 | Mismo evento dos veces | Un correo (inbox) |

## Al cerrar la fase

Logs historial + evidencia correo (o mock SMTP).

**Pregunta:** *¿Confirmas Fase 5 OK para Fase 6 (MS-4)?*

---

# FASE 6 — MS-4 Calificaciones

## Alcance

**Desde:** MS-4 usa gRPC a MS-1, MS-2, MS-3, MS-6.  
**Hasta:** JWT local; tablas **proyección** materia/alumno; consume eventos MS-2/MS-3/MS-1; publica eventos calificaciones; notificaciones de cierre vía bus (MS-6 consume `materia.calificaciones_cerradas.v1` o `materia.closed.v1`).

**No incluye:** MS-5 ni MS-7.

## Compose mínimo

```text
rabbitmq, db-auth, ms-auth, db-periodos, ms-periodos, db-alumnos, ms-alumnos
db-calificaciones, ms-calificaciones, workers outbox+consumer
db-notificaciones, ms-notificaciones (solo si pruebas correo cierre)
```

## Tareas (checklist)

- [ ] Modelos `MateriaProjection`, `AlumnoMateriaProjection` (+ migraciones).
- [ ] Consumidores eventos upstream; inbox.
- [ ] Backfill inicial (comando único): cargar proyección desde datos ya existentes en BD MS-4 o snapshot documentado.
- [ ] Publicar: `actividad.created.v1`, `calificacion.updated.v1`, `concentrado.calculado.v1`, `materia.calificaciones_cerradas.v1`.
- [ ] Quitar gRPC validación alumno/materia en views.
- [ ] Quitar gRPC a MS-6 en cierre.
- [ ] Tests calificar/cerrar con MS-2/MS-3 **apagados** (proyección ya poblada).

## Prueba individual MS-4

| # | Acción | Resultado esperado |
|---|--------|-------------------|
| 1 | Tras backfill, listar/calificar | OK sin gRPC MS-2/MS-3 |
| 2 | Cerrar materia | Evento en bus; MS-6 opcional envía correo |
| 3 | Apagar MS-6 | Cierre en MS-4 igualmente 200 |

## Al cerrar la fase

Estado proyección + ejemplo evento publicado.

**Pregunta:** *¿Confirmas Fase 6 OK para Fase 7 (MS-5)?*

---

# FASE 7 — MS-5 Asistencias QR

## Alcance

**Desde:** MS-5 valida con gRPC MS-1 y MS-3 en cada escaneo.  
**Hasta:** JWT local; proyección alumno/materia/periodo; publica eventos asistencia; Redis solo anti-replay/TTL.

**No incluye:** MS-7.

## Compose mínimo

```text
rabbitmq, redis, db-asistencias, ms-asistencias, workers
(+ MS-2/MS-3 solo para emitir eventos de prueba o backfill proyección)
```

## Tareas (checklist)

- [ ] Proyecciones + consumidores eventos MS-2/MS-3.
- [ ] Backfill proyección (comando documentado).
- [ ] Publicar: `asistencia.registered.v1`, `asistencia.rejected.v1`, `qr.session.created.v1`, etc.
- [ ] Outbox si publicación tras registrar asistencia.
- [ ] Cola local opcional si broker caído (mismo patrón outbox).
- [ ] Eliminar gRPC MS-3 en escaneo.

## Prueba individual MS-5

| # | Acción | Resultado esperado |
|---|--------|-------------------|
| 1 | Escanear QR válido | Asistencia guardada; evento en Rabbit |
| 2 | Materia cerrada en proyección | Rechazo + `asistencia.rejected.v1` |
| 3 | MS-3 apagado | Escaneo OK si proyección actualizada |

## Al cerrar la fase

**Pregunta:** *¿Confirmas Fase 7 OK para Fase 8 (MS-7)?*

---

# FASE 8 — MS-7 Reportes & Stats

## Alcance

**Desde:** MS-7 agrega por gRPC a MS-2, MS-3, MS-4, MS-5.  
**Hasta:** Proyecciones locales alimentadas por eventos; Excel/PDF desde BD MS-7; respuesta API con `data_as_of`; comando `rebuild_projections`.

**No incluye:** retirar código gRPC muerto del repo (Fase 9).

## Compose mínimo

```text
rabbitmq + todos los productores de eventos relevantes O replay de eventos desde archivo de prueba
db-reportes, ms-reportes, ms-reportes-worker-consumer
```

## Tareas (checklist)

- [ ] Esquema proyecciones (materias, alumnos, calificaciones, asistencia).
- [ ] Consumidores todos los eventos del CATALOG que apliquen.
- [ ] Backfill / rebuild desde cero.
- [ ] Refactor `report_data_service` sin gRPC.
- [ ] JWT local.
- [ ] Tests: generar reporte con MS-4 y MS-5 apagados.

## Prueba individual MS-7

| # | Acción | Resultado esperado |
|---|--------|-------------------|
| 1 | Tras eventos de prueba, GET reporte | Archivo/metadata OK |
| 2 | `data_as_of` presente | Timestamp coherente |
| 3 | Apagar MS-2…MS-5 | Reporte sigue con proyección local |

## Al cerrar la fase

**Pregunta:** *¿Confirmas Fase 8 OK para Fase 9 (cierre)?*

---

# FASE 9 — Cierre: retiro gRPC, documentación y sistema completo

## Alcance

**Desde:** sistema híbrido (flags, gRPC legacy).  
**Hasta:** `USE_EVENT_BUS=true` por defecto; sin llamadas gRPC de negocio; `CONTEXTO_GLOBAL_PROYECTO.md` con reglas R1–R8; prueba E2E documentada.

## Tareas (checklist)

- [ ] Buscar y eliminar o marcar `@deprecated` clientes gRPC de negocio en MS-2…MS-7.
- [ ] Actualizar diagrama arquitectura (Nginx + 7 MS + RabbitMQ).
- [ ] `docs/runbooks/EVENT_BUS_OPERATIONS.md` (DLQ, replay, lag).
- [ ] CI: servicio Rabbit + test integración mínimo.
- [ ] Prueba E2E manual documentada (flujo: login → materia → alumno → calificación → asistencia → reporte → correo).
- [ ] Tabla registro de avance al inicio del doc: todas las fases ✅.

## Prueba sistema completo

```text
docker compose up (perfil full)
```

Escenario único documentado en `docs/EVIDENCIA_BUS_E2E.md` (crear si no existe).

## Al cerrar la fase

Resumen final + lista de gRPC eliminados.

**Pregunta:** *¿Confirmas migración bus de eventos COMPLETA?*

---

# Referencia técnica (no es una fase; consulta durante implementación)

## Reglas arquitectónicas finales (R1–R8)

| Regla | Descripción |
|-------|-------------|
| R1 | Una BD MySQL por MS; sin acceso cruzado |
| R2 | Cliente → REST vía Nginx |
| R3 | Integración entre dominios = eventos RabbitMQ + outbox |
| R4 | Sin gRPC en negocio ni efectos secundarios |
| R5 | gRPC solo admin/soporte si queda documentado |
| R6 | JWT validado localmente en cada MS |
| R7 | Consumidores idempotentes (inbox) |
| R8 | Productores con outbox (at-least-once sin pérdida post-commit) |

## Sobre de evento

```json
{
  "event_id": "uuid",
  "event_name": "alumno.importado.v1",
  "event_version": 1,
  "aggregate_type": "alumno",
  "aggregate_id": "12345",
  "source_service": "ms-alumnos",
  "correlation_id": "uuid",
  "causation_id": "uuid",
  "occurred_at": "2026-05-22T12:00:00Z",
  "payload": {}
}
```

## Tablas outbox / inbox

Ver SQL en versiones anteriores del plan (sección outbox/inbox); mismas tablas en cada MS que publique o consuma.

## Inventario gRPC a eliminar (por fase)

| Fase | Elimina |
|------|---------|
| 3 | MS-2 → MS-1 ValidateToken |
| 4 | MS-3 → MS-6; reduce MS-3 → MS-1 sync |
| 5 | MS-6 ← MS-3/MS-4 llamadas; MS-6 → MS-2/MS-3 |
| 6 | MS-4 → MS-1/2/3/6 negocio |
| 7 | MS-5 → MS-1/3 |
| 8 | MS-7 → MS-2/3/4/5 |
| 9 | Limpieza restos y protos si aplica |

## Anti-patrones

- Publicar antes del commit.
- Bloquear HTTP esperando correo o consumidor.
- gRPC “rápido” en lugar de proyección.
- Ack del bus solo después de SMTP (MS-6).

## Criterios de aceptación global (Fase 9)

- [ ] Cada MS opera su API principal con otros MS caídos (según tabla de prueba de su fase).
- [ ] Notificaciones y reportes asíncronos con SLA documentado.
- [ ] Sin BD cruzada; duplicados sin doble efecto; trazabilidad `correlation_id`.

---

## Para el asistente (Cursor)

Al iniciar una sesión de trabajo, preguntar: **“¿En qué fase estamos?”** y leer el checklist de esa fase solamente. Al terminar, **no avanzar** sin confirmación del usuario. Actualizar la tabla “Registro de avance” cuando el usuario confirme.

**Siguiente paso cuando el usuario diga “empezar”:** ejecutar **solo Fase 1**.
