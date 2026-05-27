# 02 — Matriz de Dependencias gRPC

**Qué MS comunica con qué, y cómo.**

---

## Matriz Consumidor → Proveedor

| # | Consumidor | Proveedor | Método RPC | Puerto | Estado |
|----|-----------|-----------|-----------|--------|--------|
| 1 | ms-calificaciones | ms-alumnos | `GetAlumnoById` | 50053 | ✅ Testeado |
| 2 | ms-calificaciones | ms-auth | `ValidateToken` | 50051 | ✅ Implementado |
| 3 | ms-asistencias | ms-alumnos | `GetAlumnoById` | 50053 | ✅ Testeado |
| 4 | ms-asistencias | ms-auth | `ValidateToken` | 50051 | ✅ Implementado |
| 5 | ms-periodos | ms-auth | `ValidateToken` | 50051 | ✅ Implementado |
| 6 | ms-notificaciones | ms-alumnos | `GetAlumnoById` | 50053 | ✅ Implementado |
| 7 | ms-notificaciones | ms-periodos | `GetMateriaById` | 50052 | ✅ Implementado |
| 8 | ms-reportes | ms-alumnos | `GetAlumnosByMateria` | 50053 | ✅ Implementado |
| 9 | ms-reportes | ms-periodos | `GetMateriaById` | 50052 | ✅ Implementado |
| 10 | ms-reportes | ms-calificaciones | (integración directa) | 50054 | ✅ Existe |

**Leyenda:**
- ✅ **Testeado:** incluido en smoke tests o tests unitarios
- ✅ **Implementado:** código escrito y Docker builds correctamente
- 📋 **Planificado:** documentado, no ejecutado aún

---

## Detalle de Flujos por Microservicio

### MS-1 (Auth) — Proveedor
**Puerto:** 50051  
**Métodos:**
- `ValidateToken(token) → ValidateTokenResponse` — valida JWT
- `GetUserById(user_id) → User` — obtiene datos de usuario
- `CheckRole(user_id, role) → CheckRoleResponse` — verifica rol

**Consumidores:** ms-periodos, ms-calificaciones, ms-asistencias, ms-notificaciones

---

### MS-2 (Periodos) — Proveedor
**Puerto:** 50052  
**Métodos:**
- `GetMateriaById(materia_id) → Materia`
- `GetMateriasByDocente(docente_id) → MateriasResponse`
- `GetPeriodoActivo() → Periodo`

**Consumidores:** ms-notificaciones, ms-reportes, ms-calificaciones (opcional)

---

### MS-3 (Alumnos) — Proveedor (MÁS USADO)
**Puerto:** 50053  
**Métodos:**
- `GetAlumnoById(alumno_id) → Alumno` ← **testeado en ms-calificaciones, ms-asistencias**
- `GetAlumnosByMateria(materia_id) → AlumnosResponse`
- `IsAlumnoEnMateria(alumno_id, materia_id) → bool`

**Consumidores:** ms-calificaciones, ms-asistencias, ms-notificaciones, ms-reportes

---

### MS-4 (Calificaciones) — Proveedor / Consumidor
**Puerto:** 50054  
**Métodos (provee):**
- `GetCalificacionesPorAlumno(alumno_id) → CalificacionesResponse`
- `CreateCalificacion(...)` (interno)

**Métodos (consume):**
- `GetAlumnoById` → ms-alumnos
- `ValidateToken` → ms-auth

---

### MS-5 (Asistencias) — Proveedor / Consumidor
**Puerto:** 50055  
**Métodos (provee):**
- `GetAsistenciasPorAlumno(alumno_id) → AsistenciasResponse`

**Métodos (consume):**
- `GetAlumnoById` → ms-alumnos ← **testeado**
- `ValidateToken` → ms-auth

---

### MS-6 (Notificaciones) — Consumidor
**Puerto:** 50056  
**Métodos (provee):**
- `SendBienvenida(alumno_id, ...) → SendResponse`
- `SendBaja(alumno_id, ...) → SendResponse`
- `SendCierreMateria(materia_id) → SendResponse`

**Métodos (consume):**
- `GetAlumnoById` → ms-alumnos
- `GetMateriaById` → ms-periodos

---

### MS-7 (Reportes) — Consumidor (MÁS CONSUMIDOR)
**Puerto:** 50057  
**Métodos (provee):**
- `GenerateReport(materia_id, ...) → ReportResponse`
- `GetHistorialDocente(docente_id) → HistorialResponse`

**Métodos (consume):**
- `GetAlumnosByMateria` → ms-alumnos
- `GetMateriaById` → ms-periodos
- (Cálculos internos con BD calificaciones y asistencias)

---

## Tabla de Canales y Timeouts

| Consumidor | Proveedor | Host Env Var | Port Env Var | Timeout (default) |
|-----------|-----------|-------------|-------------|------------------|
| ms-calificaciones | ms-alumnos | `MS_ALUMNOS_GRPC_HOST` | `MS_ALUMNOS_GRPC_PORT` | 5s |
| ms-calificaciones | ms-auth | `MS_AUTH_GRPC_HOST` | `MS_AUTH_GRPC_PORT` | 5s |
| ms-asistencias | ms-alumnos | `MS_ALUMNOS_GRPC_HOST` | `MS_ALUMNOS_GRPC_PORT` | 5s |
| ms-reportes | * | `MS_ALUMNOS_GRPC_HOST` etc. | `MS_*_GRPC_PORT` | 30s (calificaciones) |

**Valor por defecto en Docker Compose:**
- `MS_ALUMNOS_GRPC_HOST = ms-alumnos`
- `MS_ALUMNOS_GRPC_PORT = 50053`
- etc.

---

## Verificación de Conectividad

Dentro de Docker:

```bash
# Desde ms-calificaciones, verificar canal a ms-alumnos
docker compose exec ms-calificaciones sh -lc "nc -zv ms-alumnos 50053"
# Expected: Connection to ms-alumnos 50053 port [tcp/*] succeeded!

# Hacer llamada real
docker compose exec ms-calificaciones sh -lc \
  "python -c \"import sys; sys.path.insert(0, '/app'); from grpc_clients import get_alumno_by_id; print(get_alumno_by_id(1))\""
```

---

## Resumen: Pares Críticos (Demostración)

Para la **presentación del proyecto**, estos 3+ pares deben funcionar:

1. ✅ **ms-calificaciones → ms-alumnos** (`GetAlumnoById`)
   - Test: `docker compose exec ms-calificaciones sh -lc "cd /app && python tests/test_grpc_utils.py"`

2. ✅ **ms-asistencias → ms-alumnos** (`GetAlumnoById`)
   - Test: `docker compose exec ms-asistencias sh -lc "cd /app && python tests/test_grpc_utils.py"`

3. ✅ **ms-calificaciones → ms-auth** (`ValidateToken`)
   - Test: mapeo de `StatusCode.UNAUTHENTICATED` → `PermissionError` en `grpc_utils.py`
