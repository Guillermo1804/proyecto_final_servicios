# Estado_Cero.md — AGM Gestión Académica FCC BUAP

> **INMUTABLE.** Creado en: 2026-05-16. No editar después del primer sprint.
> Fuente de verdad de arquitectura, stack real y deuda técnica inicial.

---

## 1. Propósito Real del Proyecto

Sistema de gestión académica para la Facultad de Ciencias de la Computación (FCC) de la BUAP.
Gestiona periodos escolares, materias, docentes, alumnos, calificaciones, asistencias QR y reportes.
Usuarios finales: administradores FCC, docentes y alumnos.
Contexto: proyecto final de Ingeniería de Software — evaluación académica con entrega y demo.

| Capacidad | Estado Real | Evidencia |
|---|---|---|
| Infraestructura Docker | ✅ Completa | `docker-compose.yml` con 7 MySQL + Redis + Nginx |
| Scaffolds Django | ✅ Completos | 7 MS con Dockerfile, entrypoint, requirements |
| Contratos gRPC | ✅ Completos | 7 archivos `.proto` bien definidos |
| Frontend Angular | ✅ Scaffoldeado | Screens para 3 roles, routing parcial |
| Lógica de negocio | ❌ 0% | 0 models, 0 views, 0 serializers en cualquier MS |
| Tests | ❌ 0% | Ningún MS tiene código de aplicación |
| gRPC servicers | ❌ 0% | `grpc_server/__init__.py` vacíos en todos los MS |

---

## 2. Stack Tecnológico Completo

| Capa | Tecnología | Versión | Notas |
|---|---|---|---|
| Backend | Django | >=5.0,<7.0 | Todos los MS |
| API REST | Django REST Framework | >=3.15 | Todos los MS |
| Auth tokens | djangorestframework-simplejwt | >=5.3 | Todos los MS |
| CORS | django-cors-headers | >=4.3 | Todos los MS |
| BD driver | mysqlclient | >=2.2 | Todos los MS |
| gRPC | grpcio + grpcio-tools | >=1.60 | Todos los MS |
| Config | python-decouple | >=3.8 | Todos los MS |
| WSGI | gunicorn | >=21.2 | Todos los MS |
| BD | MySQL | 8.0 | utf8mb4 — 7 instancias independientes |
| Cache / Anti-replay | Redis | 7-alpine | Solo ms-asistencias |
| PDF parse | pdfplumber | >=0.10 | ms-periodos, ms-alumnos |
| Excel parse | openpyxl + pandas | >=3.1 / >=2.2 | ms-alumnos, ms-calificaciones |
| PDF gen | reportlab | >=4.1 | ms-reportes |
| Frontend | Angular | ^20.3.0 | standalone components, signals |
| UI | Angular Material | ^20.2.14 | |
| Icons | Bootstrap Icons | ^1.13.1 | |
| QR scan | html5-qrcode | ^2.3.8 | |
| Reactive | RxJS | ~7.8.0 | |
| CSS | SCSS | — | |
| Gateway | Nginx | 1.25-alpine | Puerto 8080 |
| Containers | Docker Compose | — | |
| Deploy | Railway | — | URLs `agm-*.up.railway.app` |
| Runtime Python | Python | 3.x (Dockerfile) | |
| Runtime Node | Node 20+ | — | Build Angular |
| TypeScript | TypeScript | ~5.9.2 | |

---

## 3. Mapa Topológico del Codebase

```
AGM/
├── docker-compose.yml          # Orquestación: 7 MySQL + Redis + 7 MS + Nginx
├── docker/nginx/default.conf   # Gateway: rutas /api/[ms]/ → upstream interno
├── proto/                      # Contratos gRPC (BOUNDARY CRÍTICO — no modificar sin aprobación)
│   ├── auth.proto              # AuthService: ValidateToken, GetUserById, CheckRole, CreateUser
│   ├── periodos.proto          # PeriodosService: GetMateriaById, GetMateriasByDocente, GetPeriodoActivo
│   ├── alumnos.proto           # AlumnosService: GetAlumnosByMateria, GetAlumnoById, IsAlumnoEnMateria, GetDocenteByUsuarioId
│   ├── calificaciones.proto    # CalificacionesService: GetConcentrado, GetPromedioAlumno, GetEstadisticasMateria
│   ├── asistencias.proto       # AsistenciasService: GetAsistenciaAlumno, GetEstadisticasAsistencia
│   ├── notificaciones.proto    # NotificacionesService: SendBienvenida, SendBajaNotif, SendCierreMateria, SendResetPassword
│   └── reportes.proto          # ReportesService: GenerateReport, GetHistorialDocente
├── ms-auth/                    # MS-1 | REST:8001 gRPC:50051 | agm_auth_db
│   ├── apps/core/              # ← VACÍO (0 models, 0 views)
│   ├── grpc_server/            # ← VACÍO
│   ├── grpc_clients/           # ← VACÍO
│   └── proto_generated/        # Stubs generados (excluidos de git)
├── ms-periodos/                # MS-2 | REST:8002 gRPC:50052 | agm_periodos_db | pdfplumber
├── ms-alumnos/                 # MS-3 | REST:8003 gRPC:50053 | agm_alumnos_db | pdfplumber+openpyxl+pandas
├── ms-calificaciones/          # MS-4 | REST:8004 gRPC:50054 | agm_calificaciones_db | openpyxl
├── ms-asistencias/             # MS-5 | REST:8005 gRPC:50055 | agm_asistencias_db + Redis | redis+cryptography
├── ms-notificaciones/          # MS-6 | REST:8006 gRPC:50056 | agm_notificaciones_db
├── ms-reportes/                # MS-7 | REST:8007 gRPC:50057 | agm_reportes_db | openpyxl+reportlab
│   (todos los MS tienen idéntica estructura interna de scaffold)
├── frontend/sistema_AGM/       # Angular 20 — screens para 3 roles
│   ├── src/app/screens/admin-screen/    # periodos, materias, docentes
│   ├── src/app/screens/docente-screen/  # materias, asistencias, calificaciones, reportes
│   ├── src/app/screens/alumno-screen/   # notas, horario, perfil
│   ├── src/app/services/facade.service.ts  # ← ÚNICO punto de entrada HTTP (implementar)
│   └── src/app/app.routes.ts            # ← Routing parcial (sin guards implementados)
├── docs/
│   ├── CONTEXTO_GLOBAL_PROYECTO.md  # Fuente de verdad de reglas de negocio
│   ├── backlog_AGM_completo.md      # Backlog completo (Epics 1-11, ~1144 líneas)
│   ├── microservicios/MS1-MS7*.md   # Especificación técnica por MS
│   └── devs/Alan/                   # Skills y planes de acción (este sistema)
└── test-data/                       # Seeds BUAP: alumnos_buap.csv, trabajadores_buap.csv, SQLs, PDFs
    ├── seed_alumnos_mysql.sql
    ├── seed_docentes_mysql.sql
    └── *.pdf                        # Programas académicos reales para pruebas de import
```

---

## 4. Vulnerabilidades y Deuda Técnica Inicial

### 🔴 Crítico

| ID | Descripción | MS afectado | Riesgo |
|---|---|---|---|
| DT-001 | 0 models.py en todos los MS — sistema no funcional | Todos | Bloquea cualquier sprint de negocio |
| DT-002 | 0 gRPC servicers implementados — ningún MS puede recibir llamadas inter-MS | Todos | MS-1 bloquea el resto |
| DT-003 | 0 endpoints REST — Nginx gateway no puede enrutar nada útil | Todos | Frontend sin backend |
| DT-004 | MS-1 no implementado — todos los demás MS dependen de `ValidateToken` | ms-auth | Desbloquea toda la cadena |
| DT-005 | Constraint periodo único activo no implementada — riesgo de doble activo en MySQL | ms-periodos | Corrupción de datos silenciosa |

### 🟠 Alto

| ID | Descripción | MS afectado | Riesgo |
|---|---|---|---|
| DT-006 | `facade.service.ts` sin métodos HTTP — Angular no puede comunicarse con el backend | frontend | Frontend bloqueado |
| DT-007 | Guards de rol no implementados — rutas sin protección por rol | frontend | Acceso sin autorización |
| DT-008 | `GetDocenteByNombre` ausente en `alumnos.proto` — import PDF de MS-2 no puede resolver `docente_id` | ms-periodos, ms-alumnos | Datos incompletos en import |
| DT-009 | Anti-replay QR no implementado — Redis disponible pero sin lógica | ms-asistencias | Asistencias duplicadas |
| DT-010 | 0 tests en todos los MS — no hay baseline numérico | Todos | Sin red de seguridad para refactors |

### 🟡 Medio

| ID | Descripción | MS afectado | Riesgo |
|---|---|---|---|
| DT-011 | `urls.py` en todos los MS solo tiene `/admin/` — router DRF vacío | Todos | Normal en scaffold inicial |
| DT-012 | Desalineación potencial de `docente_id` entre MS-2 y MS-3 — convención no documentada en código | ms-periodos, ms-alumnos | FK lógica inconsistente |
| DT-013 | `.env.example` existe pero `.env` real no está en el repo — setup no automatizado | Todos | Fricción en onboarding |
| DT-014 | `proto_generated/` excluido de git — requiere `./generate_proto.sh` en cada clon | Todos | Fricción en CI y máquinas nuevas |
| DT-015 | Frontend usa Angular 20 (más reciente) — documentación de APIs puede no coincidir con versiones viejas | frontend | Riesgo de deprecaciones |

---

## 5. Dependencias de Implementación (secuencia forzada)

```
MS-1 (auth)
  └─→ MS-2 (periodos) — necesita ValidateToken
       └─→ MS-3 (alumnos) — necesita ValidateToken + GetMateriaById
            ├─→ MS-4 (calificaciones) — necesita IsAlumnoEnMateria
            ├─→ MS-5 (asistencias)    — necesita IsAlumnoEnMateria + Redis
            └─→ MS-6 (notificaciones) — necesita GetDocenteByUsuarioId
                 └─→ MS-7 (reportes)  — necesita GetConcentrado + GetEstadisticasAsistencia
```

MS-4, MS-5, MS-6 pueden desarrollarse en paralelo una vez MS-3 esté funcional.
MS-7 es el último en la cadena.
