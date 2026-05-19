# Guía y plan de acción — Cierre de código AGM

**Alcance:** solo código (backend, gateway, integraciones gRPC, frontend).  
**Excluido:** despliegue cloud, video, manuales PDF, checklist de entrega académica.  
**Fecha de referencia:** 2026-05-18  
**Estado global estimado (código E2E):** ~99%

**Documentos relacionados:** `docs/RESUMEN_CAMBIOS.md`, `docs/backlog_AGM_completo.md`, `docs/postman/AGM_API_Collection.json`

---

## 1. Resumen ejecutivo

| Capa | % actual | Meta |
|------|----------|------|
| Backend (7 MS, REST + gRPC + tests) | ~99% | 100% |
| Integración MS ↔ MS (gRPC Docker) | ~99% | 100% |
| Gateway Nginx ↔ MS | ~99% | 100% |
| Frontend ↔ API (`FacadeService`) | ~98% | ≥95% |
| **Sistema código punta a punta** | **~99%** | **≥95%** |

Los 7 MS pasan tests en Docker (156+). MS-1 arranca gRPC con espera de puerto + healthcheck REST+gRPC; los demás MS esperan `ms-auth` healthy. Sin pantalla CRUD usuarios (admin vía API/seed). Pendiente opcional: pulido UX Epic 10 y marcar matriz E2E manual §6.

---

## 2. Estado actual por microservicio

### 2.1 Backend individual

| MS | Puerto REST | gRPC | Tests | Backend |
|----|-------------|------|-------|---------|
| MS-1 Auth | 8001 / `:8080/auth` | 50051 | 14 | ✅ ~98% |
| MS-2 Periodos | 8002 | 50052 | 13 | ✅ ~98% |
| MS-3 Alumnos | 8003 | 50053 | 24 | ✅ ~98% |
| MS-4 Calificaciones | 8004 | 50054 | 24 | ✅ ~98% |
| MS-5 Asistencias | 8005 | 50055 | 10 | ✅ ~95% |
| MS-6 Notificaciones | 8006 | 50056 | 20 | ✅ ~98% |
| MS-7 Reportes | 8007 | 50057 | 34 | ✅ ~98% |

### 2.2 Integración entre MS (ya cableada en código)

| Origen | Destino | Uso |
|--------|---------|-----|
| MS-1 | MS-6 | `SendResetPassword` (forgot/reset) |
| MS-3 | MS-1 | `CreateUser` al importar alumnos |
| MS-3 | MS-2 | `GetMateriaById` / enriquecimiento |
| MS-3 | MS-6 | `SendBienvenida`, `SendBajaNotif` |
| MS-4 | MS-1 | `ValidateToken` |
| MS-4 | MS-3 | alumnos por materia / `IsAlumnoEnMateria` |
| MS-4 | MS-6 | `SendCierreMateria` |
| MS-5 | MS-1 | JWT (`MsJwtAuthentication` / gRPC) |
| MS-6 | MS-1, MS-2, MS-3 | datos para plantillas |
| MS-7 | MS-1…MS-5 | reportes y estadísticas |

### 2.3 Frontend — matriz pantalla ↔ API (actualizada)

| Pantalla | Ruta | API real | Estado |
|----------|------|----------|--------|
| Login | `/login` | MS-1 | ✅ |
| Logout (topbar) | — | MS-1 | ✅ |
| Forgot / Reset password | `/forgot-password`, `/reset-password` | MS-1 | ✅ |
| Admin periodos | `/admin/periodos` | MS-2 | ✅ |
| Admin materias | `/admin/materias` | MS-2 CRUD + filtro periodo | ✅ |
| Admin docentes | `/admin/docentes` | MS-3 + reset MS-1 | ✅ |
| Admin dashboard | `/admin/dashboard` | MS-2/3 | ✅ |
| Admin usuarios | — | MS-1 API | ➖ sin UI (por diseño; seed/API) |
| Docente materias | `/docente/materias` | MS-2 + stats MS-7 | ✅ |
| Docente detalle materia | `/docente/materias/:id` | MS-3/4/5 | ✅ |
| Docente calificaciones | `/docente/calificaciones` | MS-4 | ✅ |
| Docente asistencias | `/docente/asistencias` | MS-5 vía gateway | ✅ |
| Docente reportes | `/docente/reportes` | MS-7 | ✅ |
| Docente dashboard / rendimiento | `/docente/dashboard`, `…/rendimiento` | MS-2/4/7 | ✅ |
| Alumno horario / notas / QR / perfil / dashboard | `/alumno/*` | MS-3/4/5/7 | ✅ |

---

## 3. Inventario de lo faltante (detallado)

### 3.1 ~~Crítico — Gateway Nginx (MS-5)~~ ✅ resuelto

Rutas `/sesiones/`, `/qr/`, `/registros/`, `/asistencias/` con `rewrite` a `/api/...` en `docker/nginx/default.conf` (Fase 1).

### 3.1b MS-1 gRPC en Docker ✅ resuelto

- `ms-auth/entrypoint.sh`: gRPC en background + `wait_grpc_port.sh` antes de Gunicorn.
- Healthcheck MS-1: REST `/health/` **y** puerto `50051`.
- `docker-compose.yml`: MS-2…MS-7 `depends_on: ms-auth: service_healthy`.

**Verificación:**

```powershell
docker compose up -d nginx ms-asistencias ms-auth
# Con JWT en variable (tras login Postman o frontend)
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8080/sesiones/activa/?materia_id=1"
# Esperado: 200 o 404 de negocio, NO 404 HTML de Django por ruta inexistente
```

Actualizar `scripts/smoke-gateway.ps1` para incluir `/registros/` y distinguir 404 de ruta vs 401/403.

---

### 3.2 Crítico — Flujo asistencias alumno (QR)

| Ítem | Backend | Frontend |
|------|---------|----------|
| Generar QR dinámico | `GET /api/qr/generate/?materia_id=&alumno_id=` ✅ | ❌ |
| Pantalla alumno con renovación ~30 s | — | ❌ |
| Ruta Angular | — | ❌ no existe en `alumno.routes.ts` |

**Tareas código:**

1. `FacadeService`: `generateQr(materiaId, alumnoId): Observable<...>`
2. Nueva pantalla `qr-asistencia-screen` (o integrar en dashboard alumno)
3. `interval(30000)` o similar para refrescar QR
4. Ruta `/alumno/qr` + enlace en `bottom-navbar-alumno`
5. Resolver `alumno_id` desde JWT / `GET /auth/me` + relación MS-3 si hace falta

**Verificación:** docente inicia sesión → escanea QR generado en app alumno → `POST /asistencias/registrar/` → registro en lista.

---

### 3.3 Alto — Pantallas con mock → API real

#### Admin dashboard (`admin-screen/dashboard-screen`)

| Dato mock | API sugerida |
|-----------|--------------|
| Total alumnos / docentes / materias | agregar endpoints o contar listados: `listDocentes`, `listMaterias`, MS-3 |
| Periodo activo | `getPeriodoActivo()` |

#### Docente dashboard (`docente-screen/dashboard-screen`)

| Dato mock | API sugerida |
|-----------|--------------|
| Clases del día | `listMaterias` filtradas por docente + horario si existe en modelo |
| % asistencia hoy | `registrosAsistenciaHoy(materiaId)` MS-5 (tras fix gateway) |
| KPIs | `getEstadisticasDocente(getUserId())` MS-7 |

#### Alumno dashboard (`alumno-screen/dashboard-screen`)

| Dato mock | API sugerida |
|-----------|--------------|
| Materias hoy | `getMisMateriasAlumno()` MS-3 |
| Resumen | `getEstadisticasAlumno(alumnoId)` MS-7 |

#### Rendimiento docente (`rendimiento-screen`)

| Dato mock | API sugerida |
|-----------|--------------|
| Estudiantes en riesgo | `getConcentrado(materiaId)` MS-4 + umbral promedio &lt; 6 |
| % asistencia | MS-5 o stats en concentrado |

---

### 3.4 Alto — Completar módulos con API lista pero UI incompleta

#### Notas alumno (`notas-screen`)

- Hoy: carga materias MS-3; `promedio: 0`, parciales `'--'`.
- Falta: por cada `materia_id`, llamar `getConcentrado(materiaId)` o endpoint alumno MS-4 si existe RBAC.
- Archivos: `notas-screen.ts`, posible método `FacadeService.getMisCalificaciones(materiaId)`.

#### Detalle materia — tab evaluación (`detalle-materia-screen`)

- Hoy: `rubrosEvaluacion` hardcodeado.
- Falta: `getPonderaciones` / `savePonderaciones` / `listActividades` (ya en `FacadeService`).
- Archivos: `detalle-materia-screen.ts`, `.html`.

#### Admin materias (`materias-screen`)

- Hoy: solo `listMaterias`.
- Falta: formulario alta/edición con `createMateria()`; filtro `periodo_id` en query.

#### Forgot / Reset password

- Backend MS-1: `POST /auth/forgot-password`, `POST /auth/reset-password` ✅
- Interceptor ya excluye rutas públicas en `auth.interceptor.ts`.
- Falta: `forgot-password-screen`, `reset-password-screen`, rutas en `app.routes.ts`, métodos en `FacadeService`.

#### Baja de materia (alumno)

- Backend: `POST /api/alumnos/{id}/baja-materia/` con body `{ materia_id }` ✅
- Falta: método `FacadeService.bajaMateria(alumnoId, materiaId)` + UI modal confirmación en notas o detalle.

#### Reset password docente (admin)

- Backend: `POST /usuarios/{id}/reset-password` MS-1 ✅
- Falta: botón en `docentes-screen` + llamada Facade.

#### Cerrar materia (docente)

- `FacadeService.cerrarMateriaCalificaciones()` existe; verificar si `calificaciones-screen` o `detalle-materia` lo invocan. Si no, añadir botón + modal.

---

### 3.5 Medio — Backend / integración

| ID | Descripción | Archivo / zona |
|----|-------------|----------------|
| BE-01 | Worker/cron cierre sesión TTL Redis → MySQL | `ms-asistencias` (management command o Celery; opcional MVP) |
| BE-02 | Enriquecer listado registros con nombre alumno (gRPC MS-3) | `ms-asistencias` views/serializers |
| BE-03 | Alinear filtro materias docente: `docente_usuario_id` vs PK `Docente` | MS-2 list + frontend `listMaterias({ docente_id })` |
| BE-04 | RBAC docente: solo alumnos de sus materias en `por-materia` | `ms-alumnos` views |
| BE-05 | Eliminar `auth.service.ts` duplicado o redirigir a `FacadeService` | `frontend/.../auth.service.ts` |
| BE-06 | Revisar `perfil-screen` alumno: conectar `getMe()` | `alumno-screen/perfil-screen` |

---

### 3.6 Bajo — Calidad de código

| Ítem | Acción |
|------|--------|
| Actualizar `Deuda_Tecnica.md` | Reflejar MS-4/5/10 cerrados en backend; mover pendientes a esta guía |
| Postman MS-5 | Tras fix nginx, re-ejecutar carpeta Asistencias vía `:8080` |
| Tests E2E manuales | Tabla §6 de este documento |

---

## 4. Plan de acción por fases

### Fase 0 — Preparación (0,5 día)

| # | Tarea | Responsable | Hecho |
|---|--------|-------------|-------|
| 0.1 | `docker compose up -d` stack completo | — | [ ] *(ejecutar en tu máquina)* |
| 0.2 | Login admin/docente/alumno; guardar 3 JWT en Postman | — | [ ] |
| 0.3 | Baseline tests: `docker exec agm-ms-* python manage.py test ...` (ver `RESUMEN_CAMBIOS.md`) | — | [ ] |
| 0.4 | Anotar `materia_id`, `alumno_id`, `docente_usuario_id` de seed local | — | [ ] |

---

### Fase 1 — Desbloqueo gateway MS-5 (0,5–1 día) — **CRÍTICO** ✅ código

| # | Tarea | Archivos | Hecho |
|---|--------|----------|-------|
| 1.1 | Añadir `rewrite` + `location /registros/` en Nginx | `docker/nginx/default.conf` | [x] |
| 1.2 | Reiniciar nginx: `docker compose restart nginx` | — | [ ] *(local)* |
| 1.3 | Probar flujo Postman MS-5 vía `{{base_url_gateway}}` | `docs/postman/` | [ ] |
| 1.4 | Probar `asistencias-screen` en navegador | `asistencias-screen.ts` | [ ] |
| 1.5 | Actualizar `scripts/smoke-gateway.ps1` | `scripts/` | [x] |

**% ganado estimado:** +8% E2E global

---

### Fase 2 — Flujo alumno QR + baja (1–2 días) ✅ código

| # | Tarea | Archivos | Hecho |
|---|--------|----------|-------------------|
| 2.1 | `generateQr()` en Facade | `facade.service.ts` | [x] |
| 2.2 | Pantalla QR con timer 30 s | `alumno-screen/qr-asistencia-screen` | [x] |
| 2.3 | Ruta + navbar alumno | `alumno.routes.ts`, navbar | [x] |
| 2.4 | `bajaMateriaAlumno()` en Facade | `facade.service.ts` | [x] |
| 2.5 | Botón baja en notas | `notas-screen` | [x] |
| 2.6 | Prueba E2E: alumno QR → docente escanea → registro | manual | [ ] |

**% ganado estimado:** +10% E2E

---

### Fase 3 — Completar calificaciones y notas (1–2 días) ✅ código

| # | Tarea | Archivos | Hecho |
|---|--------|----------|-------------------|
| 3.1 | `notas-screen`: cargar concentrado MS-4 por materia | `notas-screen.ts` | [x] |
| 3.2 | Tab evaluación en detalle materia: ponderaciones + actividades | `detalle-materia-screen.*` | [x] |
| 3.3 | Botón cerrar materia | `calificaciones-screen.*` | [x] |
| 3.4 | Admin materias: crear + filtro periodo | `materias-screen.*` | [x] |
| 3.5 | Tests regresión MS-4 | `ms-calificaciones` | [x] *(24 tests OK en Docker)* |

**% ganado estimado:** +8% E2E

---

### Fase 4 — Auth UX + admin docentes (1 día) ✅ código

| # | Tarea | Archivos | Hecho |
|---|--------|----------|-------------------|
| 4.1 | Pantallas forgot / reset | `forgot-password-screen`, `reset-password-screen` | [x] |
| 4.2 | Reset password docente desde admin | `docentes-screen.ts` | [x] |
| 4.3 | Eliminar `auth.service.ts` legacy | — | [x] |
| 4.4 | `perfil-screen`: `getMe()` + datos alumno | `perfil-screen.*` | [x] |

**% ganado estimado:** +5% E2E

---

### Fase 5 — Dashboards sin mock (1–2 días) ✅ código

| # | Tarea | Archivos | Criterio de listo |
|---|--------|----------|-------------------|
| 5.1 | Admin dashboard con APIs | `admin/dashboard-screen.*` | [x] KPIs count MS-2/3 |
| 5.2 | Docente dashboard | `docente/dashboard-screen.*` | [x] materias + stats MS-7 |
| 5.3 | Alumno dashboard | `alumno/dashboard-screen.*` | [x] inscripciones + stats MS-7 |
| 5.4 | Rendimiento docente | `rendimiento-screen.*` | [x] riesgo MS-4 concentrado |
| 5.5 | Filtro materias por docente (BE-03) | `ms-periodos` + pantallas docente | [x] `?docente_id=` |

**% ganado estimado:** +12% E2E

---

### Fase 6 — Pulido backend opcional (0,5–1 día) ✅ código

| # | Tarea | Prioridad | Hecho |
|---|--------|-----------|-------|
| 6.1 | BE-02 nombres en registros asistencia | Media | [x] |
| 6.2 | BE-04 RBAC docente por-materia | Media | [x] |
| 6.3 | BE-01 cron cierre sesión | Baja | [x] `cerrar_sesiones_expiradas` |
| 6.4 | Actualizar `docs/RESUMEN_CAMBIOS.md` matriz FE | Alta | [x] |
| 6.5 | Sincronizar `Deuda_Tecnica.md` | Media | [x] |

---

## 5. Checklist por microservicio (código)

### MS-1 Auth
- [x] REST + gRPC + tests
- [x] UI forgot / reset
- [x] UI reset docente (admin)
- [x] Sin `auth.service.ts` duplicado
- [x] UI perfil alumno (`getMe`)

### MS-2 Periodos
- [x] REST + gRPC + tests + FE periodos
- [x] FE crear materia + filtro periodo (admin)

### MS-3 Alumnos
- [x] REST + gRPC + tests + FE docentes/import/detalle alumnos
- [x] FE baja materia alumno
- [x] RBAC docente `por-materia` (titular MS-2)

### MS-4 Calificaciones
- [x] REST + gRPC + tests + FE calificaciones docente
- [x] FE notas alumno (MS-4 concentrado)
- [x] FE ponderaciones en detalle materia
- [x] FE cerrar materia (calificaciones-screen)

### MS-5 Asistencias
- [x] REST + gRPC + tests
- [x] Nginx rewrite `/api/` (Fase 1)
- [x] location `/registros/`
- [x] FE QR alumno
- [x] Nombres en listado registros (gRPC MS-3)
- [x] Comando `cerrar_sesiones_expiradas`

### MS-6 Notificaciones
- [x] Integrado vía gRPC desde MS-1/3/4
- [ ] Sin tareas FE (interno)

### MS-7 Reportes
- [x] REST + gRPC + tests + FE reportes
- [ ] FE stats en dashboards / rendimiento
- [ ] `getEstadisticasAlumno` en UI alumno

---

## 6. Matriz de verificación E2E (código)

Ejecutar tras cada fase. Stack: `docker compose up -d`, frontend `npm start`, gateway `:8080`.

| # | Rol | Flujo | MS involucrados | OK |
|---|-----|-------|-----------------|-----|
| E1 | Admin | Login → crear periodo → activar → import PDF materias | 1, 2 | [ ] |
| E2 | Admin | Listar/import docentes PDF | 1, 3 | [ ] |
| E3 | Docente | Listar materias → detalle → import alumnos preview/confirm | 2, 3 | [ ] |
| E4 | Docente | Ponderaciones + actividades + concentrado + editar nota | 4 | [ ] |
| E5 | Docente | Import Excel calificaciones → publicar lista | 4 | [ ] |
| E6 | Docente | Iniciar sesión asistencia → escanear QR alumno → ver registro | 5 | [ ] |
| E7 | Alumno | Ver QR renovándose cada 30 s | 5 | [ ] |
| E8 | Alumno | Ver notas reales por materia | 3, 4 | [ ] |
| E9 | Alumno | Baja materia (irreversible) | 3, 6 | [ ] |
| E10 | Docente | Export PDF/Excel reportes + ver estadísticas | 7 | [ ] |
| E11 | Cualquiera | Forgot → email (log MS-6) → reset password | 1, 6 | [ ] |
| E12 | Docente | Cerrar materia → notificación alumnos (MS-6) | 4, 6 | [ ] |

---

## 7. Comandos útiles

```powershell
# Stack
docker compose up -d
docker compose restart nginx

# Tests por MS
docker exec agm-ms-auth python manage.py test apps.core.tests
docker exec agm-ms-periodos python manage.py test apps.core.tests
docker exec agm-ms-alumnos python manage.py test apps.core.tests
docker exec agm-ms-calificaciones python manage.py test apps.core.tests
docker exec agm-ms-asistencias python manage.py test apps.core.tests tests.test_grpc_utils
docker exec agm-ms-notificaciones python manage.py test apps.notificaciones.tests
docker exec agm-ms-reportes python manage.py test apps.reportes.tests

# gRPC upstream MS-7
docker exec agm-ms-reportes python manage.py verify_grpc_upstream --materia-id 1 --docente-usuario-id 2

# Frontend
cd frontend/sistema_AGM
npm start
```

---

## 8. Orden recomendado (resumen)

```
Fase 0 Preparación
    ↓
Fase 1 Nginx MS-5          ← desbloquea asistencias docente
    ↓
Fase 2 QR alumno + baja    ← cierra módulo asistencias E2E
    ↓
Fase 3 Notas + ponderaciones + admin materias
    ↓
Fase 4 Forgot/reset + admin reset docente
    ↓
Fase 5 Dashboards sin mock
    ↓
Fase 6 Pulido opcional
```

**Esfuerzo total estimado:** 5–8 días-persona (1 dev full-stack) para llegar a **≥95% código E2E**.

---

## 9. Referencia rápida — `FacadeService` sin usar en UI

Implementar consumo en pantallas o eliminar si no aplica:

| Método | Uso previsto |
|--------|----------------|
| `getPonderaciones` / `savePonderaciones` | detalle-materia tab evaluación |
| `listActividades` | detalle-materia / calificaciones |
| `cerrarMateriaCalificaciones` | calificaciones o detalle |
| `createMateria` | admin materias |
| `getEstadisticasAlumno` | alumno dashboard / notas |
| `registrosAsistenciaHoy` | docente dashboard |
| `generateQr` *(añadir)* | pantalla QR alumno |
| `bajaMateria` *(añadir)* | notas alumno |
| `forgotPassword` / `resetPassword` *(añadir)* | auth screens |

---

*Documento generado para cierre de integración código. Actualizar checkboxes al completar cada ítem.*
