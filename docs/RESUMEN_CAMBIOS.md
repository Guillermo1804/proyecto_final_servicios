# Resumen de cambios — AGM Backend + Frontend

**Documento único de pulido:** avance por MS, integración frontend, pruebas y Postman. No crear `MATRIZ_PRUEBAS_*.md` aparte — todo va aquí.

**Gateway local:** `http://localhost:8080`  
**Frontend:** `frontend/sistema_AGM` → `environment.apiBaseUrl`  
**Postman:** `docs/postman/AGM_API_Collection.json` (Login MS-1 → `{{jwt_token}}`)

---

## Pruebas automatizadas (resumen)

| MS | Comando | Tests |
|----|---------|-------|
| MS-1 | `docker exec agm-ms-auth python manage.py test apps.core.tests` | 14 OK (T1–T10 REST + gRPC) |
| MS-2 | `docker exec agm-ms-periodos python manage.py test apps.core.tests` | 13 OK (T1–T13) |
| MS-3 | `docker exec agm-ms-alumnos python manage.py test apps.core.tests` | 24 OK |
| MS-4 | `docker exec agm-ms-calificaciones python manage.py test apps.core.tests` | 24 OK |
| MS-5 | `docker exec agm-ms-asistencias python manage.py test apps.core.tests tests.test_grpc_utils` | 10 OK |
| MS-6 | `docker exec agm-ms-notificaciones python manage.py test apps.notificaciones.tests` | 20 OK (P1–P10) |
| MS-7 | `docker exec agm-ms-reportes python manage.py test apps.reportes.tests` | 34 OK (R1–R10) |

<details>
<summary>MS-1 — casos T1–T10</summary>

| ID | Caso | ✅ |
|----|------|---|
| T1 | Login admin | `test_t1_login_admin` |
| T2 | `me` sin token → 401 | |
| T3 | Refresh válido | |
| T4 | Logout + blacklist refresh | |
| T5 | Forgot password (200) | mock MS-6 |
| T6 | Reset token válido | |
| T7 | Reset token reusado → 400 | |
| T8 | gRPC token inválido | |
| T9 | CreateUser duplicado | |
| T10 | Alumno `GET /usuarios` → **403** | |

</details>

<details>
<summary>MS-2 — casos T1–T13</summary>

| ID | Caso | ✅ |
|----|------|---|
| T1–T2 | Crear periodo / activar desactiva anterior | |
| T3–T4 | Import PDF OK / tolerante fallos | |
| T5 | GET periodo activo | |
| T6–T7 | Sin JWT → 401 / rol → 403 | |
| T8–T11 | Materias paginado, filtros, crear, page&limit | |
| T12–T13 | gRPC GetPeriodoActivo / GetMateriaById NOT_FOUND | |

</details>

<details>
<summary>MS-6 — casos P1–P10</summary>

Bienvenida, baja docente, cierre materia, reset password, SMTP error, REST sin API key → 401, CORS, health. Suite: `apps.notificaciones.tests`.

</details>

<details>
<summary>MS-7 — casos R1–R10</summary>

Excel/PDF calificaciones y asistencias, stats docente/alumno RBAC, formato inválido 400, gRPC GenerateReport, sin JWT 401, docente no titular 403, health. Suite: `apps.reportes.tests`.

</details>

---

## Matriz de conexión Frontend ↔ Backend

| MS | Pantalla(s) | Endpoint gateway | Estado integración |
|----|-------------|------------------|-------------------|
| MS-1 | Login, logout (topbar) | `/auth/*` | ✅ Conectado |
| MS-2 | Admin periodos, materias | `/periodos/`, `/materias/` | ✅ Listados + crear/activar/import PDF |
| MS-3 | Admin docentes, import alumnos, detalle materia | `/docentes/`, `/alumnos/*` | ✅ Conectado (pulido 18/05) |
| MS-3 | Alumno horario/notas | `/alumnos/me/materias/` | ✅ Conectado |
| MS-4 | Docente calificaciones | `/concentrado/`, `/calificaciones/`, ponderaciones | ✅ Conectado (pulido 18/05) |
| MS-5 | Docente asistencias | `/sesiones/`, `/qr/`, `/registros/` | ✅ + nombres alumno en lista |
| MS-1 | Forgot/reset, perfil | `/forgot-password`, `/alumno/perfil` | ✅ |
| MS-2/7 | Dashboards admin/docente/alumno | varios | ✅ Fase 5 |
| MS-7 | Docente reportes | `/reportes/`, `/estadisticas/` | ✅ Conectado (repaso 18/05) |
| MS-6 | (interno) | `/notificaciones/` | N/A frontend |
| MS-7 | Docente reportes, rendimiento | `/reportes/`, `/estadisticas/` | ✅ Conectado (descarga + stats) |

**Transversal:** `auth.interceptor` inyecta `Bearer` desde `FacadeService` (tokens `agm_*`). Guards `authGuard` + `roleGuard` activos.

### Archivos frontend modificados (2026-05-18)

- `services/facade.service.ts` — API unificada vía gateway
- `services/auth.interceptor.ts` — rutas públicas auth
- `screens/login-screen` — sin cambios (ya OK)
- `partials/topbar-admin` — logout API
- `admin-screen/periodos-screen`, `materias-screen`
- `docente-screen/materias-screen`, `reportes-screen`
- `alumno-screen/notas-screen`, `horario-screen`
- `admin-screen/docentes-screen`, `docente-screen/importar-alumnos-screen`, `detalle-materia-screen` (lista alumnos)
- `docente-screen/calificaciones-screen` (concentrado, edición notas, import Excel, imprimir lista)

---

## MS-1 — Auth & Users ✅

**Fecha pulido:** 2026-05-18  
**Epic:** 3 (ISSUE-301 … 308)

### Backend

| Entregable | Estado |
|------------|--------|
| REST login / refresh / me / logout / forgot / reset | ✅ |
| CRUD `/usuarios` + API key `POST /usuarios` | ✅ |
| gRPC `:50051` (ValidateToken, GetUserById, CheckRole, CreateUser) | ✅ |
| Tests T1–T10 (`apps.core.tests`) | ✅ 14 passed |
| README `ms-auth/README.md` | ✅ |
| Postman carpeta **MS-1 Auth** | ✅ |
| Backlog 301–308 marcado | ✅ |

### Correcciones

- Import `transaction` en `reset-password` (bug 500).
- `GET /usuarios` → 403 para no-admin autenticado (antes 401).
- `grpc_servicer.py` + `ValidateToken` vía **SimpleJWT TokenBackend** (misma clave que login).
- `proto_generated` en `sys.path` (`settings.py`).
- `requirements.txt`: `protobuf>=6.31`, `grpcio>=1.70`.

### Frontend

| Componente | Cambio |
|------------|--------|
| `login-screen` | Ya usaba `FacadeService.login` → gateway ✅ |
| `auth.guard` / `roleGuard` | Ya activos ✅ |
| `auth.interceptor` | Rutas excluidas corregidas (`refresh-token`) |
| `topbar-admin` | Logout llama API `POST /auth/logout` + `clearSession` |
| `FacadeService` | `logout`, `getMe`, `getUserId`, métodos MS-2/3/4/7 |
| Pantallas admin/docente/alumno | Listados y descargas vía API (ver matriz arriba) |

### Pendiente MS-1 frontend

- Pantalla forgot/reset password (solo API lista).
- Unificar `auth.service.ts` (duplicado legacy `:8001`) → usar solo `FacadeService`.

---

## MS-2 — Periodos & Materias ✅

**Fecha pulido:** 2026-05-18  
**Epic:** 4 (ISSUE-401 … 408)

### Backend

| Entregable | Estado |
|------------|--------|
| CRUD periodos + activar (un solo activo) | ✅ |
| Import PDF `POST /periodos/:id/importar-materias/` | ✅ |
| CRUD materias + paginación/filtros | ✅ |
| gRPC `:50052` (3 RPC) | ✅ |
| JWT vía MS-1 (`utils/auth.py`) | ✅ |
| `GET /periodos/activo/` público | ✅ |
| Tests T1–T13 (`apps.core.tests`) | ✅ 13 OK |
| README `ms-periodos/README.md` | ✅ |
| Postman carpeta **MS-2 Periodos** (gateway) | ✅ |
| Backlog 401–408 marcado | ✅ |

### Frontend

| Componente | Cambio |
|------------|--------|
| `FacadeService` | `createPeriodo`, `activarPeriodo`, `importarMateriasPdf`, `createMateria` |
| `periodos-screen` | Crear periodo, activar, import PDF, búsqueda local |
| `materias-screen` | Listado API (sin cambios adicionales) |

### Pendiente MS-2 frontend

- CRUD materias en UI (alta/edición manual).
- Filtro por `periodo_id` en listado materias admin.

---

## MS-3 — Docentes & Alumnos ✅

**Fecha pulido:** 2026-05-18 · Epic 5 (ISSUE-501 … 509)

### Backend

| Entregable | Estado |
|------------|--------|
| CRUD docentes + import PDF | ✅ |
| Import alumnos preview/confirmar + inscripción por `materia_id` | ✅ |
| `GET /alumnos/por-materia/` | ✅ |
| `GET /alumnos/me/materias/` enriquecido MS-2 | ✅ |
| Baja materia + notificación MS-6 | ✅ |
| gRPC `:50053` (3 RPC) | ✅ |
| Tests (`apps.core.tests`) | ✅ 24 OK |
| README `ms-alumnos/README.md` | ✅ |
| Postman **MS-3 Alumnos** (gateway) | ✅ |
| Backlog 501–509 marcado | ✅ |

### Frontend

| Pantalla | Cambio |
|----------|--------|
| `docentes-screen` | Listado API + import PDF |
| `importar-alumnos-screen` | Preview CSV/XLSX + confirmar con `materia_id` |
| `detalle-materia-screen` | Tab alumnos vía `por-materia` |
| `FacadeService` | `listDocentes`, `importDocentesPdf`, preview/confirm import, fix `por-materia` |

### Pendiente MS-3

- ~~RBAC docente solo ve alumnos de sus materias~~ → ✅ `por-materia` valida titular MS-2 (19/05).

---

## MS-4 — Calificaciones & Ponderaciones ✅

**Fecha pulido:** 2026-05-18 · Epic 6 (ISSUE-601 … 609)

### Backend

| Entregable | Estado |
|------------|--------|
| Ponderaciones CRUD + import Excel (suma 100 %) | ✅ |
| Actividades + calificaciones upsert/import | ✅ |
| `GET /concentrado/:materia_id` enriquecido MS-3 | ✅ |
| Cierre materia + imprimir lista (bloqueo edición) | ✅ |
| gRPC `:50054` | ✅ |
| Tests `apps.core.tests` | ✅ 24 OK (fix clase anidada en tests) |
| README `ms-calificaciones/README.md` | ✅ |
| Postman **MS-4 Calificaciones** | ✅ |
| Backlog 601–609 | ✅ |

### Frontend

| Pantalla | Cambio |
|----------|--------|
| `calificaciones-screen` | Selector materia, concentrado API, columnas dinámicas, blur guarda nota, import Excel, publicar lista |
| `FacadeService` | ponderaciones, actividades, upsert, import, cerrar, imprimir-lista |

### Pendiente MS-4

- UI configuración ponderaciones/actividades en `detalle-materia` (evaluación tab).
- Pantalla alumno consulta calificaciones propias.

---

## MS-5 — Asistencias QR ✅

**Fecha pulido:** 2026-05-18 · Epic 7 (ISSUE-701 … 708)

### Backend

| Entregable | Estado |
|------------|--------|
| JWT vía MS-1 (`MsJwtAuthentication`) | ✅ |
| Sesiones iniciar/cerrar/activa + stats Redis/MySQL | ✅ |
| QR HMAC + anti-replay + `POST /asistencias/registrar/` | ✅ |
| Consultas registros (hoy, historial, por alumno) | ✅ |
| gRPC `:50055` | ✅ |
| Tests `apps.core.tests` + `tests.test_grpc_utils` | ✅ (ver tabla pruebas) |
| README `ms-asistencias/README.md` | ✅ |
| Postman **MS-5 Asistencias** | ✅ |
| Backlog 701–708 | ✅ |

### Frontend

| Pantalla | Cambio |
|----------|--------|
| `asistencias-screen` | Selector materia, iniciar/cerrar sesión, stats en vivo, scanner → registrar QR, lista registros |
| `FacadeService` | sesiones, stats, registros, registrar QR |

### Pendiente MS-5

- ~~Portal alumno QR~~ → ✅ `/alumno/qr` (Fase 2).
- Cron en producción: programar `cerrar_sesiones_expiradas` (comando listo).
- ~~Enriquecer lista con nombre alumno~~ → ✅ gRPC MS-3 (Fase 6).

---

## MS-6 — Notificaciones ✅

**Fecha pulido:** 2026-05-17 · repaso SMTP 2026-05-18 · Epic 8 · **20 tests OK** (P1–P10)

| Entregable | Estado |
|------------|--------|
| `EmailService` + plantillas HTML | ✅ |
| SMTP Gmail (`sistemasagm2026@gmail.com` en `.env`, no en repo) | ✅ |
| `USE_PLACEHOLDER_DATA=False` → `GrpcDataProvider` (MS-2/MS-3) | ✅ |
| gRPC `:50056` + REST `/notificaciones/*` | ✅ |
| Comando `send_test_email` | ✅ |
| Postman MS-6 + `INTERNAL_API_KEY` | ✅ |

Sin pantalla Angular. README `ms-notificaciones/README.md`.

**Verificar correo real:**
```bash
docker compose up -d ms-notificaciones ms-alumnos ms-periodos
docker compose restart ms-notificaciones
docker exec agm-ms-notificaciones python manage.py send_test_email --to sistemasagm2026@gmail.com
```

---

## MS-7 — Reportes y Estadísticas ✅

**Fecha pulido:** 2026-05-17 · repaso gRPC real 2026-05-18 · Epic 9 (ISSUE-901 … 907) · **34 tests OK** (R1–R10)

| Entregable | Estado |
|------------|--------|
| Reportes PDF/Excel calificaciones + asistencias | ✅ |
| `GET /estadisticas/docente|alumno` | ✅ |
| gRPC `:50057` (`GenerateReport`, `GetHistorialDocente`) | ✅ |
| Clientes MS-1…MS-5 | ✅ |
| `USE_MOCK_DATA=False` en `.env` Docker (gRPC real MS-4/MS-5) | ✅ |
| Comando `verify_grpc_upstream` | ✅ |
| Postman **MS-7** | ✅ |
| Frontend `reportes-screen` (stats API + export calif/asist) | ✅ |

**Verificar datos reales (stack levantado):**
```bash
docker compose up -d ms-reportes ms-auth ms-periodos ms-alumnos ms-calificaciones ms-asistencias
docker compose restart ms-reportes
docker exec agm-ms-reportes python manage.py verify_grpc_upstream --materia-id 1 --docente-usuario-id 2
```

README `ms-reportes/README.md`.

---

## Cómo verificar integración rápida

```powershell
docker compose up -d
cd frontend/sistema_AGM
npm start
# Login: admin@agm.buap.mx / admin123
```

1. Login → redirige por rol.
2. Admin → Periodos / Materias muestran datos del API (o lista vacía).
3. Docente → Reportes → Generar PDF/Excel descarga archivo.
4. Alumno → Notas carga materias desde `/alumnos/me/materias/`.
