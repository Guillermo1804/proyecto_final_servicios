# Deuda_Tecnica.md — AGM Gestión Académica FCC BUAP

> **DOCUMENTO VIVO.** Actualizar únicamente al cierre de cada sprint exitoso.
> No crear documentos adicionales de backlog. No eliminar ítems — tachar con ~~texto~~.

---

## Sprint History

| ID | MS | Descripción | Scope violations | Tests inicio→cierre | Intentos | Correcciones |
|---|---|---|---|---|---|---|
| S-01 | ms-periodos | ISSUE-401+402: Modelos Periodo/Materia + CRUD periodos + constraint único activo | none | 0→2 passed; 0 failed | 1 | 0 |
| S-02 | ms-periodos | ISSUE-403: Import PDF materias — pdfplumber, upsert por NRC, tolerante a fallos | none | 2→4 passed; 0 failed | 1 | 0 |
| S-03 | ms-periodos | ISSUE-404: CRUD materias — MateriaViewSet, filtros dinámicos, paginación AGM envelope | none | 4→7 passed; 0 failed | 1 | 0 |
| S-04 | ms-periodos | ISSUE-408: Paginación ?page&limit — AGMPagination explícito, PeriodoViewSet+MateriaViewSet estandarizados | none | 7→8 passed; 0 failed | 1 | 0 |
| S-05 | ms-periodos | ISSUE-405: Servidor gRPC :50052 — GetMateriaById, GetMateriasByDocente, GetPeriodoActivo | none | 8→10 passed; 0 failed | 1 | 0 |
| S-06 | ms-periodos | ISSUE-407: GET /api/periodos/activo/ — endpoint público validado | none | 10→11 passed; 0 failed | 1 | 0 |
| S-07 | ms-alumnos | ISSUE-501: Modelos Docente/Alumno/Inscripcion + constraint unicidad funcional MySQL | none | 0→3 passed; 0 failed | 1 | 0 |
| S-08 | ms-alumnos | ISSUE-503: CRUD docentes — ViewSet, filtros icontains, paginación AGM envelope | none | 3→6 passed; 0 failed | 1 | 0 |
| S-09 | ms-alumnos | ISSUE-504: Import alumnos — pandas/openpyxl, preview/confirm, upsert, gRPC mock | none | 6→9 passed; 0 failed | 1 | 0 |
| S-10 | ms-alumnos | ISSUE-505: Listado alumnos por materia — filter materia_id, select_related, activos only | none | 9→11 passed; 0 failed | 1 | 0 |
| S-11 | ms-alumnos | ISSUE-506: Baja de materia — irreversible logic, fecha_baja field, gRPC SendBajaNotif mock | none | 11→13 passed; 0 failed | 1 | 0 |
| S-12 | ms-alumnos | ISSUE-507: Servidor gRPC :50053 — GetAlumnosByMateria, GetAlumnoById, IsAlumnoEnMateria | none | 13→15 passed; 0 failed | 1 | 0 |
| S-13 | docs | ISSUE-1104: Colección Postman — 22 endpoints (MS-2 y MS-3) + Environment | none | N/A | 0 | 0 |
| S-14 | ms-notificaciones | Epic 8 ISSUE-801–806: EmailService, REST, gRPC :50056, integración MS-1/3/4 | none | 0→20 passed; 0 failed | 1 | 0 |
| S-15 | ms-reportes | Epic 9 ISSUE-901–907: REST reportes/stats, gRPC :50057, clientes MS-1..5, mocks MS-4/5 | none | 0→34 passed; 0 failed | 1 | 0 |
| S-16 | ms-periodos | ISSUE-406: JWT en ms-periodos — @jwt_required decorator, ValidateToken via gRPC, mock auth [13 tests] | none | 11→13 passed; 0 failed | 1 | 0 |
| S-17 | ms-alumnos | ISSUE-509: JWT en ms-alumnos — @jwt_required decorator, ValidateToken via gRPC, auth fix [18 tests] | none | 16→18 passed; 0 failed | 1 | 0 |

---

## Backlog Activo

### 🏗️ Epic 1 — Infraestructura & DevOps
**Responsable:** Makinohara

| Issue | Descripción | Estado | Prioridad |
|---|---|---|---|
| ISSUE-101 | Setup inicial entornos Docker Compose + `.env` por MS | 🔴 activo | Alta |
| ISSUE-102 | Pipeline CI/CD básico (GitHub Actions) | 🔴 activo | Media |
| ISSUE-103 | Deploy Railway — 7 MS en HTTPS | 🔴 activo | Alta |
| ISSUE-104 | Nginx gateway: routing por prefijo `/api/[ms]/` | 🟡 pendiente | Alta |

---

### 🔐 Epic 3 — MS-1 Auth & Users
**Responsable:** Gerardo

| Issue | Descripción | Estado | Prioridad |
|---|---|---|---|
| ISSUE-301 | Modelos `Usuario` + migraciones MySQL | 🔴 activo | **CRÍTICA — desbloquea todo** |
| ISSUE-302 | `POST /api/auth/login/` — JWT access+refresh | 🔴 activo | Crítica |
| ISSUE-303 | `POST /api/auth/refresh/` | 🔴 activo | Crítica |
| ISSUE-304 | `POST /api/auth/logout/` | 🔴 activo | Alta |
| ISSUE-305 | Servidor gRPC :50051 — `ValidateToken`, `GetUserById`, `CheckRole` | 🔴 activo | **CRÍTICA** |
| ISSUE-306 | gRPC `CreateUser` — para imports de MS-3 | 🔴 activo | Alta |
| ISSUE-307 | `POST /api/auth/reset-password/` | 🟡 pendiente | Media |
| ISSUE-308 | Seed usuario admin inicial | 🔴 activo | Alta |

---

### 📐 Epic 2 — Arquitectura gRPC
**Responsable:** Guillermo

| Issue | Descripción | Estado | Prioridad |
|---|---|---|---|
| ISSUE-201 | Definir convención de `docente_id` entre MS-2 y MS-3 (DT-012) | 🔴 activo | Alta |
| ISSUE-202 | Decidir: agregar `GetDocenteByNombre` a `alumnos.proto` o resolución por nombre en MS-2 (DT-008) | 🔴 activo | Alta |
| ISSUE-203 | Documentar mapa de llamadas inter-MS en Manual Técnico | 🟡 pendiente | Media |

---

### 📅 Epic 4 — MS-2 Periodos & Materias
**Responsable:** Alan

| Issue | Descripción | Estado | Prioridad |
|---|---|---|---|
| ~~ISSUE-401~~ | ~~Modelos `Periodo`, `Materia` + migraciones + constraint único activo~~ | ✅ cerrado | Alta |
| ~~ISSUE-402~~ | ~~CRUD periodos con `select_for_update` en activación~~ | ✅ cerrado | Alta |
| ~~ISSUE-403~~ | ~~Import PDF materias (pdfplumber, tolerante a fallos, upsert por NRC)~~ | ✅ cerrado | Alta |
| ~~ISSUE-404~~ | ~~CRUD materias con paginación y búsqueda~~ | ✅ cerrado | Alta |
| ~~ISSUE-405~~ | ~~Servidor gRPC :50052 — 3 RPCs de `periodos.proto`~~ | ✅ cerrado | Alta |
| ~~ISSUE-406~~ | ~~JWT via gRPC MS-1 en todos los endpoints~~ | ✅ cerrado | Alta |
| ~~ISSUE-407~~ | ~~`GET /api/periodos/activo/` — endpoint público o autenticado~~ | ✅ cerrado | Media |
| ~~ISSUE-408~~ | ~~Paginación `?page&limit` en listados~~ | ✅ cerrado | Alta |

---

### 👥 Epic 5 — MS-3 Docentes & Alumnos
**Responsable:** Alan

| Issue | Descripción | Estado | Prioridad |
|---|---|---|---|
| ~~ISSUE-501~~ | ~~Modelos `Docente`, `Alumno`, `InscripcionMateria` + migraciones~~ | ✅ cerrado | Alta |
| ISSUE-502 | Import PDF docentes → `CreateUser` MS-1 + seed `Docente` | 🔴 activo | Alta |
| ~~ISSUE-503~~ | ~~CRUD docentes con paginación~~ | ✅ cerrado | Alta |
| ~~ISSUE-504~~ | ~~Import alumnos Excel/CSV con preview + confirmación + `SendBienvenida`~~ | ✅ cerrado | Alta |
| ~~ISSUE-505~~ | ~~Listado alumnos por materia (solo activos)~~ | ✅ cerrado | Alta |
| ~~ISSUE-506~~ | ~~Baja de materia — irreversible, `SendBajaNotif` gRPC MS-6~~ | ✅ cerrado | Alta |
| ~~ISSUE-507~~ | ~~Servidor gRPC :50053 — 4 RPCs de `alumnos.proto`~~ | ✅ cerrado | Alta |
| ISSUE-508 | `GET /api/alumnos/me/materias/` enriquecido con MS-2 | 🟡 pendiente | Media |
| ~~ISSUE-509~~ | ~~JWT via gRPC MS-1 en todos los endpoints~~ | ✅ cerrado | Alta |

---

### 📊 Epic 6 — MS-4 Calificaciones & Ponderaciones
**Responsable:** Guillermo

| Issue | Descripción | Estado | Prioridad |
|---|---|---|---|
| ISSUE-601 | Modelos `Categoria`, `Actividad`, `Calificacion` + migraciones | 🔴 activo | Alta |
| ISSUE-602 | CRUD categorías con validación ponderaciones = 100 | 🔴 activo | Alta |
| ISSUE-603 | CRUD actividades por categoría | 🔴 activo | Alta |
| ISSUE-604 | Ingresar/editar calificaciones por alumno | 🔴 activo | Alta |
| ISSUE-605 | Concentrado de calificaciones (promedio real + redondeado) | 🔴 activo | Alta |
| ISSUE-606 | Import calificaciones desde Excel | 🟡 pendiente | Media |
| ISSUE-607 | Servidor gRPC :50054 — 3 RPCs de `calificaciones.proto` | 🔴 activo | Alta |
| ~~ISSUE-608~~ | ~~`POST /materias/:id/cerrar` → `SendCierreMateria` gRPC MS-6~~ | ✅ cerrado | Alta |

---

### 📋 Epic 7 — MS-5 Asistencias QR
**Responsable:** Guillermo

| Issue | Descripción | Estado | Prioridad |
|---|---|---|---|
| ISSUE-701 | Modelos `Sesion`, `RegistroAsistencia` + migraciones | 🔴 activo | Alta |
| ISSUE-702 | Generar QR con token Redis (TTL 10 min) | 🔴 activo | Alta |
| ISSUE-703 | Registro asistencia alumno — anti-replay `SET NX` Redis | 🔴 activo | Alta |
| ISSUE-704 | Listado asistencias por alumno y por materia | 🔴 activo | Alta |
| ISSUE-705 | Servidor gRPC :50055 — 2 RPCs de `asistencias.proto` | 🔴 activo | Alta |
| ISSUE-706 | Registro asistencias: retardo por tiempo (umbral configurable) | 🟡 pendiente | Media |

---

### 🔔 Epic 8 — MS-6 Notificaciones
**Responsable:** Makinohara

| Issue | Descripción | Estado | Prioridad |
|---|---|---|---|
| ~~ISSUE-801~~ | ~~Modelo `HistorialCorreo` + SMTP + fundación Django~~ | ✅ cerrado | Alta |
| ~~ISSUE-802~~ | ~~REST/gRPC bienvenida + `clave_acceso`~~ | ✅ cerrado | Alta |
| ~~ISSUE-803~~ | ~~REST/gRPC baja al docente~~ | ✅ cerrado | Alta |
| ~~ISSUE-804~~ | ~~Cierre materia masivo (ThreadPoolExecutor)~~ | ✅ cerrado | Alta |
| ~~ISSUE-805~~ | ~~Reset password REST/gRPC~~ | ✅ cerrado | Alta |
| ~~ISSUE-806~~ | ~~Servidor gRPC :50056 — 4 RPCs~~ | ✅ cerrado | Alta |

---

### 📈 Epic 9 — MS-7 Reportes & Estadísticas
**Responsable:** Makinohara

| Issue | Descripción | Estado | Prioridad |
|---|---|---|---|
| ~~ISSUE-901~~ | ~~Fundación Django, BD `agm_reportes_db`, health, entrypoint gRPC+REST~~ | ✅ cerrado | Alta |
| ~~ISSUE-902~~ | ~~Excel calificaciones `GET /reportes/calificaciones/:id`~~ | ✅ cerrado | Alta |
| ~~ISSUE-903~~ | ~~PDF calificaciones (reportlab, UTF-8)~~ | ✅ cerrado | Alta |
| ~~ISSUE-904~~ | ~~Reporte asistencias xlsx/pdf~~ | ✅ cerrado | Alta |
| ~~ISSUE-905~~ | ~~JSON estadísticas docente + comparativa~~ | ✅ cerrado | Alta |
| ~~ISSUE-906~~ | ~~JSON estadísticas alumno + RBAC~~ | ✅ cerrado | Media |
| ~~ISSUE-907~~ | ~~Servidor gRPC :50057 — `GenerateReport`, `GetHistorialDocente`~~ | ✅ cerrado | Alta |

**Deuda residual MS-7 (S-15):**

| ID | Descripción | Severidad |
|---|---|---|
| DT-MS7-01 | `USE_MOCK_DATA=True` en dev hasta MS-4/MS-5 expongan gRPC real | 🟠 |
| DT-MS7-02 | E2E binario vía gateway requiere seed materias/alumnos en MS-2/MS-3 | 🟡 |
| DT-MS7-03 | Caché `ReporteGenerado` no usado en MVP (opcional ISSUE-901) | 🟢 |
| DT-MS7-04 | Validar `ValidateToken` MS-1 estable desde red Docker MS-7 | 🟡 |

---

### 🖥️ Epic 10 — Frontend Angular
**Responsable:** Gerardo

| Issue | Descripción | Estado | Prioridad |
|---|---|---|---|
| ISSUE-1001 | `FacadeService` con métodos HTTP para todos los MS | 🔴 activo | **CRÍTICA** |
| ISSUE-1002 | Guards de autenticación y rol | 🔴 activo | Crítica |
| ISSUE-1003 | Flujo login + persistencia JWT en localStorage | 🔴 activo | Crítica |
| ISSUE-1004 | Pantallas admin: periodos, import PDF, materias | 🔴 activo | Alta |
| ISSUE-1005 | Pantallas docente: materias, import alumnos, calificaciones, QR | 🔴 activo | Alta |
| ISSUE-1006 | Pantallas alumno: notas, horario, QR, baja | 🔴 activo | Alta |
| ISSUE-1007 | Responsive mobile (punto extra según enunciado) | 🟡 pendiente | Baja |

---

### 📄 Epic 11 — Documentación & Entregables
**Responsable:** Alan

| Issue | Descripción | Estado | Prioridad |
|---|---|---|---|
| ISSUE-1101 | README completo (instalación, integrantes, URLs prod, video) | 🟡 pendiente | Alta |
| ISSUE-1102 | Manual de usuario (PDF, 3 roles, capturas producción) | 🟡 pendiente | Alta |
| ISSUE-1103 | Manual técnico (arquitectura, ER, gRPC, APIs, despliegue) | 🟡 pendiente | Alta |
| ~~ISSUE-1104~~ | ~~Colección Postman exportada en repo~~ | ✅ cerrado | Alta |
| ISSUE-1105 | Video YouTube 10-20 min con todos los flujos | 🟡 pendiente | Alta |
| ISSUE-1106 | Checklist pre-entrega completo sin ítems pendientes | 🟡 pendiente | Crítica |

---

## Deuda Técnica Registrada (DT)

| ID | Descripción | Severidad | Estado | Sprint resuelto |
|---|---|---|---|---|
| DT-001 | 0 models en todos los MS | 🔴 | activo | ms-periodos, ms-alumnos resueltos |
| DT-002 | 0 gRPC servicers implementados | 🟡 | activo | ms-periodos, ms-alumnos resueltos |
| DT-003 | 0 endpoints REST | 🔴 | activo | ms-periodos, ms-alumnos resueltos |
| DT-004 | MS-1 no implementado — bloquea cadena completa | 🔴 | activo | — |
| DT-005 | Constraint periodo único activo sin implementar | 🔴 | activo | ms-periodos resuelto (S-01) |
| DT-006 | `facade.service.ts` sin métodos HTTP | 🟠 | activo | — |
| DT-007 | Guards de rol sin implementar | 🟠 | activo | — |
| DT-008 | `GetDocenteByNombre` ausente en `alumnos.proto` | 🟠 | activo | — |
| DT-009 | Anti-replay QR sin implementar | 🟠 | activo | — |
| DT-010 | 0 tests en todos los MS | 🟠 | activo | ms-periodos, ms-alumnos resueltos |
| DT-011 | `urls.py` con solo `/admin/` | 🟡 | activo | ms-periodos resuelto (S-01) |
| DT-012 | Desalineación potencial `docente_id` MS-2 vs MS-3 | 🟡 | activo | — |
| DT-013 | `.env` real no en repo — setup manual | 🟡 | activo | — |
| DT-014 | `proto_generated/` fuera de git — requiere script manual | 🟡 | activo | — |
| DT-015 | Angular 20 — posibles deprecaciones de APIs | 🟡 | activo | — |

---

## Baseline de Tests (inicial)

| MS | Baseline | Fecha |
|---|---|---|
| ms-auth | 0 passed; 0 failed (no tests) | 2026-05-16 |
| ms-periodos | 11 passed; 0 failed | 2026-05-16 |
| ms-alumnos | 15 passed; 0 failed | 2026-05-16 |
| ms-calificaciones | 0 passed; 0 failed (no tests) | 2026-05-16 |
| ms-asistencias | 0 passed; 0 failed (no tests) | 2026-05-16 |
| ms-notificaciones | 20 passed; 0 failed | 2026-05-17 |
| ms-reportes | 34 passed; 0 failed | 2026-05-17 |
| frontend (Angular) | 1 passed; 0 failed (app.spec.ts default) | 2026-05-16 |
