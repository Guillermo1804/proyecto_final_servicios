# AGM — Contexto global del proyecto

Documento maestro de arquitectura. Cualquier desarrollo en el monorepo debe respetar las reglas R1 a R8.

**Stack:** Django 5 + DRF (7 microservicios), MySQL 8 (una BD por MS), Redis (solo MS-5, efimero), RabbitMQ (integracion interdominio), Nginx (gateway REST).

---

## 1. Proposito del sistema

Sistema de Gestion y Automatizacion de Calificaciones (AGM) para la FCC-BUAP: periodos, materias, alumnos, calificaciones, asistencia QR, notificaciones por correo y reportes analiticos.

---

## 2. Vista de arquitectura (estado Fase 9)

```
Cliente (Angular / Postman)
        |
        | HTTP/JSON (REST)
        v
   Nginx :8080  (unico punto de entrada externo — R2)
        |
   +----+----+----+----+----+----+----+
   | MS-1 | MS-2 | MS-3 | MS-4 | MS-5 | MS-6 | MS-7 |
   | REST | REST | REST | REST | REST | REST | REST |
   +--+---+--+---+--+---+--+---+--+---+--+---+--+---+
      |      |      |      |      |      |      |
      |      +------+------+------+------+------+
      |                    |
      |            RabbitMQ (agm.domain)
      |            Outbox / Inbox por MS
      v
  JWKS MS-1 (validacion JWT local en cada MS — R6)
```

**Integracion interdominio:** exclusivamente eventos RabbitMQ con patron Outbox (productores) e Inbox (consumidores). No hay llamadas gRPC sincronicas de negocio en el hot path (R3, R4).

---

## 3. Reglas arquitectonicas (R1 a R8)

| Regla | Descripcion | Cumplimiento |
|-------|-------------|--------------|
| **R1** | Una base de datos MySQL aislada por microservicio; prohibido acceso cruzado a tablas de otro MS | Cada MS usa solo su `db-*` y modelos locales / proyecciones |
| **R2** | Clientes externos entran solo por Nginx hacia APIs REST | `docker/nginx/default.conf`, puerto host 8080 |
| **R3** | Integracion interdominio solo via RabbitMQ (eventos + outbox/inbox) | Exchange `agm.domain`, libreria `packages/agm_events` |
| **R4** | Prohibido gRPC en flujos de negocio y efectos secundarios | Clientes `grpc_clients/` bloqueados con `USE_EVENT_BUS=true` |
| **R5** | gRPC solo tareas administrativas o soporte documentadas | Servidores gRPC entrantes legacy; MS-1 reset password legacy si `USE_EVENT_BUS=false` |
| **R6** | JWT validado de forma local en cada MS via JWKS de MS-1 | `utils/jwt_local.py`, `GET /.well-known/jwks.json` |
| **R7** | Consumidores idempotentes con tabla `event_inbox` | PK `event_id`, descarte de duplicados |
| **R8** | Productores con outbox transaccional post-commit | Tabla `event_outbox`, workers `run_event_outbox` |

---

## 4. Microservicios

| MS | Nombre | REST | BD | Rol en el bus |
|----|--------|------|-----|----------------|
| MS-1 | Auth & Users | 8001 | agm_auth_db | Publica identidad; consume `user.create_requested.v1`; JWKS |
| MS-2 | Periodos & Materias | 8002 | agm_periodos_db | Publica `periodo.*`, `materia.*` |
| MS-3 | Docentes & Alumnos | 8003 | agm_alumnos_db | Publica `alumno.*`, `docente.*`; solicita usuarios a MS-1 |
| MS-4 | Calificaciones | 8004 | agm_calificaciones_db | Proyecciones MS-2/3; publica eventos calificaciones |
| MS-5 | Asistencias QR | 8005 | agm_asistencias_db + Redis | Proyecciones; publica `asistencia.*`, `qr.session.*` |
| MS-6 | Notificaciones | 8006 | agm_notificaciones_db | Solo consumidor; correos desde payloads de eventos |
| MS-7 | Reportes & Stats | 8007 | agm_reportes_db | Solo consumidor; proyecciones analiticas locales |

Catalogo de eventos: `contracts/events/CATALOG.md`.

---

## 5. gRPC — estado tras Fase 9

### Retirado del hot path (bloqueado con USE_EVENT_BUS=true)

- Validacion JWT via `ValidateToken` gRPC (MS-2 a MS-7).
- MS-3 a MS-6: bienvenida, baja, cierre por gRPC.
- MS-4 a MS-2/3/6: lecturas de negocio por gRPC.
- MS-5 a MS-1/3 en escaneo QR.
- MS-7 agregacion via gRPC a MS-2/3/4/5.

Implementacion: `packages/agm_events/agm_events/grpc_legacy.py` y guardas en modulos `grpc_clients/` / `utils/*_client.py`.

### Permitido (R5)

- Servidores gRPC **entrantes** en cada MS (compatibilidad herramientas / pruebas), sin uso en vistas REST principales.
- Ruta legacy MS-1 a MS-6 para reset de password solo si `USE_EVENT_BUS=false` (sustituida por `password.reset_requested.v1`).
- Endpoints admin MS-6: `X-Internal-Api-Key` o JWT admin via JWKS local.

Inventario detallado: `docs/GRPC_LEGACY_INVENTORY.md`.

---

## 6. Feature flag global

| Variable | Valor por defecto (Fase 9) |
|----------|---------------------------|
| `USE_EVENT_BUS` | `true` en `.env.example` raiz y de cada `ms-*/.env.example` |
| `settings.py` | `USE_EVENT_BUS = config(..., default=True)` en los 7 MS |

Con `USE_EVENT_BUS=false` quedan rutas legacy gRPC solo para desarrollo o rollback puntual (no produccion).

---

## 7. Formato REST estandar

Respuesta exitosa:

```json
{
  "success": true,
  "data": {},
  "message": "OK"
}
```

Error:

```json
{
  "success": false,
  "data": null,
  "message": "Descripcion",
  "errors": {}
}
```

Autenticacion: `Authorization: Bearer <access_token>` (RS256, claims `user_id`, `rol`, `email`).

---

## 8. Despliegue local (stack completo)

```bash
cp .env.example .env
# Copiar cada ms-*/.env.example a ms-*/.env

docker compose up --build
```

Servicios levantados: ver cabecera de `docker-compose.yml` (7 MS, 5 outbox workers, 5 consumer workers, rabbitmq, redis, 7 MySQL, nginx).

MySQL en host: puertos 13307-13313. Gateway: http://localhost:8080.

Runbook operativo del bus: `docs/runbooks/EVENT_BUS_OPERATIONS.md`.

Evidencia E2E: `docs/EVIDENCIA_BUS_E2E.md`.

---

## 9. Documentacion relacionada

| Documento | Contenido |
|-----------|-----------|
| `docs/PLAN_ACCION_BUS_EVENTOS_DESACOPLO.md` | Plan por fases (completado) |
| `contracts/events/CATALOG.md` | Eventos y consumidores |
| `contracts/events/README.md` | Politicas retry/DLQ |
| `packages/agm_events/README.md` | Libreria compartida |
| `docs/GRPC_LEGACY_INVENTORY.md` | Modulos gRPC legacy |
| `docs/runbooks/EVENT_BUS_OPERATIONS.md` | Operacion del bus |
| `docs/EVIDENCIA_BUS_E2E.md` | Prueba punta a punta |
