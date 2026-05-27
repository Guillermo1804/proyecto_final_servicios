# Evidencia E2E — Bus de eventos AGM (Fase 9)

Prueba de punta a punta con stack completo (`docker compose up --build`).

Fecha de referencia: 2026-05-23.

---

## 1. Preparacion del entorno

```powershell
cd proyecto_final_servicios
docker compose up --build -d
```

Servicios minimos para validar cadena completa: todos los definidos en `docker-compose.yml` (7 MS + workers + rabbitmq + redis + nginx).

Verificar salud:

```powershell
docker compose ps
curl http://localhost:8080/health
```

---

## 2. Flujo de prueba (7 pasos)

### Paso 1 — Login administrador (MS-1)

```http
POST http://localhost:8001/auth/login
Content-Type: application/json

{"email":"admin@agm.buap.mx","password":"admin123"}
```

Resultado esperado: `200`, `access_token` JWT RS256.

### Paso 2 — Periodo y materia (MS-2)

Con Bearer token admin:

```http
POST http://localhost:8002/periodos/
POST http://localhost:8002/materias/
```

Verificacion asincrona:

- Filas en `event_outbox` de MS-2 con `periodo.created.v1` / `materia.created.v1`.
- Tras workers: proyecciones en MS-4/MS-5/MS-7 actualizadas (consistencia eventual).

### Paso 3 — Importacion alumnos (MS-3)

```http
POST http://localhost:8003/alumnos/importar/
```

Cadena esperada:

1. MS-3 publica `alumno.imported.v1` y opcionalmente `user.create_requested.v1`.
2. MS-1 consumer crea credencial (usuario).
3. MS-6 consumer envia correo bienvenida (SMTP configurado o simulado en logs).
4. MS-4/MS-5/MS-7 actualizan proyecciones de inscripcion.

### Paso 4 — Calificaciones (MS-4)

```http
POST http://localhost:8004/... actividades y calificaciones
```

Eventos: `actividad.created.v1`, `calificacion.updated.v1`, `concentrado.calculado.v1`.

### Paso 5 — Asistencia QR (MS-5)

```http
POST sesion QR + escaneo alumno
```

Eventos: `qr.session.created.v1`, `asistencia.registered.v1` (o `asistencia.rejected.v1`).

MS-5 opera sin gRPC a MS-1/MS-3 en hot path (proyecciones locales).

### Paso 6 — Cierre de calificaciones (MS-4)

```http
POST cerrar materia (calificaciones)
```

Evento: `materia.calificaciones_cerradas.v1`.

MS-6: correo de actas cerradas via consumer (payload del evento).

### Paso 7 — Reporte analitico (MS-7)

```http
GET http://localhost:8007/estadisticas/docente/{docente_id}
Authorization: Bearer <token>
```

Resultado esperado:

- `200 OK` con metricas agregadas.
- Campo `data_as_of` en JSON y cabecera `X-AGM-Data-As-Of`.
- MS-2/MS-3/MS-4/MS-5 pueden estar detenidos; MS-7 solo lee `db-reportes`.

Comando de semilla local (desarrollo):

```bash
docker compose exec ms-reportes python manage.py rebuild_report_projections --demo-seed
```

---

## 3. Evidencias ejecutadas (Fase 8 base + Fase 9)

| Escenario | Resultado |
|-----------|-----------|
| Stack minimo MS-7 + rabbitmq + ms-auth | OK (reportes 200 con `data_as_of`) |
| Inyeccion manual `calificacion.updated.v1` / `asistencia.registered.v1` | OK (proyeccion MS-7 actualizada) |
| `USE_EVENT_BUS=true` por defecto en settings | Aplicado Fase 9 |
| Clientes gRPC negocio bloqueados | `block_business_grpc` en modulos legacy |
| MS-1 password reset via evento | `password.reset_requested.v1` en outbox |

---

## 4. Comandos de verificacion operativa

```bash
# Outbox pendiente MS-3
docker compose exec ms-alumnos python manage.py shell -c \
  "from apps.core.models import EventOutbox; print(EventOutbox.objects.filter(published_at__isnull=True).count())"

# Inbox MS-6
docker compose exec ms-notificaciones python manage.py shell -c \
  "from apps.notificaciones.models import EventInbox; print(EventInbox.objects.count())"

# Colas RabbitMQ
docker compose exec rabbitmq rabbitmqctl list_queues name messages -p agm
```

---

## 5. Criterios de aceptacion global

- [x] Cada MS opera su API principal sin depender de gRPC de negocio (con bus activo).
- [x] Notificaciones y reportes son asincronos / locales.
- [x] Sin acceso a BD cruzada; idempotencia por `event_id`.
- [x] Documentacion R1-R8 en `docs/CONTEXTO_GLOBAL_PROYECTO.md`.
- [x] Runbook en `docs/runbooks/EVENT_BUS_OPERATIONS.md`.
