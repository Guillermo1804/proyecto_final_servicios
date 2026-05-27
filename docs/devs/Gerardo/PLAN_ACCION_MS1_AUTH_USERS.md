# Plan de acción — MS-1 Auth & Users (Epic 3)

**Desarrollador:** Gerardo  
**Microservicio:** MS-1 — Auth & Users  
**Carpeta:** `/ms-auth/`  
**REST:** `8001` · **gRPC:** `50051` · **BD:** MySQL `agm_auth_db`  
**Backlog:** `docs/backlog_AGM_completo.md` — **Epic 3 (ISSUE-301 … ISSUE-308)**  
**Enunciado:** `docs/Proyecto_Final_SW_AGM.md` — §3 objetivo 3, §5.3 **Módulo 1**, §5.4.1 MS-1, §5.2 roles (login por correo)  
**Contexto:** `docs/CONTEXTO_GLOBAL_PROYECTO.md` — §4 tabla MS-1, §5 (todos consumen MS-1)  
**Especificación:** `docs/microservicios/MS1_AUTH_USERS.md`  
**Contrato:** `proto/auth.proto`

---

## 1. Rol del MS-1 en AGM

MS-1 es la **identidad centralizada** de todo el sistema:

- Autenticación por **correo + contraseña** y emisión de **JWT** (access + refresh).  
- **RBAC:** administrador, docente, alumno.  
- **Recuperación de contraseña** (token de un solo uso + integración con MS-6 para el correo).  
- **Cierre de sesión** con invalidación del refresh (blacklist).  
- **gRPC** para que **cualquier otro MS** valide tokens y roles sin tocar `agm_auth_db`.  
- **Gestión de usuarios** (admin) y **creación de usuarios** para integración MS-3 (importaciones).

Si MS-1 falla, **ningún** flujo del sistema es confiable; es el microservicio con mayor criticidad operativa.

---

## 2. Resultados medibles (“terminado”)

| # | Resultado | Evidencia |
|---|-------------|-----------|
| A1 | Usuario custom en MySQL | `AUTH_USER_MODEL` apuntando al modelo; migraciones aplicadas |
| A2 | Login / refresh / me | Postman: 200 con tokens; claims con `user_id`, `email`, `rol`, `nombre` |
| A3 | Forgot / reset password | Correo real vía MS-6; reset con token de 1 h |
| A4 | RBAC en MS-1 | Alumno 403 en ruta admin |
| A5 | gRPC AuthService | `ValidateToken`, `GetUserById`, `CheckRole`, `CreateUser` según `auth.proto` |
| A6 | MS-3 puede crear usuarios | `CreateUser` gRPC o `POST /usuarios` con API key — **una política clara** documentada |
| A7 | Logout | Refresh en blacklist no puede renovar access |

---

## 3. Contrato gRPC (`auth.proto`)

| RPC | Responsabilidad | Consumidores típicos |
|-----|-----------------|----------------------|
| `ValidateToken` | Decodificar JWT (misma `SECRET_KEY` que emisión); devolver `valid` + claims | MS-2 … MS-7 en cada request REST |
| `GetUserById` | Perfil mínimo por `user_id` | MS que muestran nombre en UI server-side |
| `CheckRole` | `user_id` + `role` → `has_role` | Autorización fina en otros MS |
| `CreateUser` | Alta con email, nombre, rol, password temporal | MS-3 importación alumnos/docentes |

**Implementación:** `AuthServiceServicer` sin métodos stub sin usar; errores gRPC coherentes (`UNAUTHENTICATED`, `NOT_FOUND`, `ALREADY_EXISTS` si aplica).

---

## 4. Endpoints REST — mapa backlog ↔ especificación

| Área | Endpoints | ISSUE |
|------|-----------|-------|
| Auth pública | `POST /auth/login`, `POST /auth/refresh-token`, `POST /auth/forgot-password`, `POST /auth/reset-password` | 302, 303 |
| Auth protegida | `GET /auth/me`, `POST /auth/logout` | 302, 308 |
| Usuarios admin | `GET/PUT/DELETE`, `POST .../reset-password` sobre `/usuarios` | 306 |
| Creación integración | `POST /usuarios` (API key interna o admin) | 307 |

**Formato JSON** del proyecto: `{ "success", "data", "message" }` en respuestas REST (salvo binarios; aquí no aplica).

---

## 5. Plan por issue (granular)

### ISSUE-301 — Proyecto base Django (MS-1)

| # | Tarea | Criterio |
|---|--------|----------|
| 301.1 | Proyecto en `/ms-auth/`, Django 5, estructura `config` + apps | `manage.py migrate` OK |
| 301.2 | Dependencias del backlog + gunicorn | `requirements.txt` con versiones |
| 301.3 | MySQL 8, `utf8mb4`, `agm_auth_db` | Conexión desde Docker |
| 301.4 | Modelo usuario: `email` único, `password` hasheado, `rol`, `nombre`, `activo` | `USERNAME_FIELD = 'email'` |
| 301.5 | `PermissionsMixin` si se usan permisos Django estándar | Coherente con MS1 doc |
| 301.6 | CORS + `ALLOWED_HOSTS` | Listo para gateway |
| 301.7 | Dockerfile + entrypoint | MS levanta en 8001 |

**Errores frecuentes:** olvidar `AUTH_USER_MODEL` antes de la primera migración; usar SQLite en prod por descuido.

---

### ISSUE-302 — Login JWT

| # | Tarea | Criterio |
|---|--------|----------|
| 302.1 | Serializer custom de `TokenObtainPair` si hace falta claims extra | Payload con `user_id`, `email`, `rol`, `nombre` |
| 302.2 | Tiempos de vida | Access 15–60 min y refresh 7 días (backlog); documentar en `.env.example` |
| 302.3 | `POST /auth/login` | 401 credenciales incorrectas; 401 usuario `activo=False` |
| 302.4 | `POST /auth/refresh-token` | Nuevo access; 401 refresh inválido |
| 302.5 | `GET /auth/me` | `JWTAuthentication`; 401 sin Bearer |

**Seguridad:** no devolver en JSON si el usuario existe en forgot-password (ver 303); en login sí distinguir 401 genérico sin filtrar existencia de email si el equipo quiere evitar enumeración (opcional).

---

### ISSUE-303 — Recuperación de contraseña

| # | Tarea | Criterio |
|---|--------|----------|
| 303.1 | Modelo `PasswordResetToken` | UUID, `expira_en` (+1 h), `usado` |
| 303.2 | `POST /auth/forgot-password` | Siempre **200** con mensaje genérico (MS1 doc regla 9 — anti-enumeración) |
| 303.3 | gRPC a MS-6 `SendResetPassword` | `email`, `token`, `reset_url` construida con `FRONTEND_URL` en env |
| 303.4 | `POST /auth/reset-password` | Validar token no usado y no expirado; hashear nueva password; marcar usado |
| 303.5 | Rate limiting opcional | Protección básica contra spam a MS-6 |

**Coordinación:** variable `MS_NOTIFICACIONES_GRPC_*` y que MS-6 esté en Compose antes de prueba E2E.

---

### ISSUE-304 — RBAC (DRF)

| # | Tarea | Criterio |
|---|--------|----------|
| 304.1 | Clases de permiso `IsAdminRole`, `IsDocenteRole`, `IsAlumnoRole` | Comprueban `request.user.rol` |
| 304.2 | Aplicar en vistas `/usuarios/*` y cualquier endpoint restringido en MS-1 | Tests o manual |
| 304.3 | Documento para otros MS | Cómo llamar `ValidateToken` + `CheckRole` desde gRPC (pegar en README técnico) |

**Nota:** la autorización en MS-2…MS-7 **no** depende solo de MS-1 en REST; cada MS debe validar el JWT vía gRPC según patrón del repo.

---

### ISSUE-305 — Servidor gRPC Auth (50051)

| # | Tarea | Criterio |
|---|--------|----------|
| 305.1 | `ValidateToken` | Aceptar token con o sin prefijo `Bearer` (normalizar una sola convención documentada) |
| 305.2 | `GetUserById` | `NOT_FOUND` si id no existe o inactivo según política |
| 305.3 | `CheckRole` | Comparación case-sensitive con valores `admin`/`docente`/`alumno` |
| 305.4 | `CreateUser` | Misma validación que REST crear usuario; email único → `CreateUserResponse.success=false` con mensaje |
| 305.5 | Arranque paralelo a Gunicorn | Puerto 50051 en `0.0.0.0` |

---

### ISSUE-306 — Gestión de usuarios (Admin)

| # | Tarea | Criterio |
|---|--------|----------|
| 306.1 | `GET /usuarios` | Paginación `page`, `limit` (§5.4.5 proyecto) |
| 306.2 | `GET /usuarios/:id` | |
| 306.3 | `PUT /usuarios/:id` | Campos permitidos: nombre, activo (no cambiar rol sin regla explícita) |
| 306.4 | `POST /usuarios/:id/reset-password` | Flujo por correo con token temporal de 1 h reutilizando MS-6 |
| 306.5 | `DELETE /usuarios/:id` | Soft delete `activo=False` |

---

### ISSUE-307 — `POST /usuarios` (integración MS-3)

| # | Tarea | Criterio |
|---|--------|----------|
| 307.1 | Header `X-Internal-Api-Key` o autenticación admin | Mismo secret en MS-3 env; rechazar 401 si falta |
| 307.2 | Body: email, nombre, rol, password | Password inicial UUID si no se envía; soporta alta desde admin |
| 307.3 | Respuesta `user_id` | MS-3 persiste FK `usuario_id` |
| 307.4 | Duplicado email | 409 o 400 con mensaje claro |

**Duplicidad con `CreateUser` gRPC:** mantener una sola capa de negocio interna invocada por REST y gRPC.

---

### ISSUE-308 — Logout / blacklist

| # | Tarea | Criterio |
|---|--------|----------|
| 308.1 | `simplejwt` blacklist app | Migraciones |
| 308.2 | `ROTATE_REFRESH_TOKENS` + blacklist | Comportamiento acordado con frontend |
| 308.3 | `POST /auth/logout` | Body con refresh; tras éxito, refresh no válido por blacklist |

**Patrón habitual:** access sigue válido hasta expiración; el enunciado “invalidación del token” se cumple para refresh y para nuevas sesiones.

---

## 6. Seguridad y cumplimiento

| Tema | Regla |
|------|--------|
| `SECRET_KEY` | Solo env; distinta prod vs dev |
| Passwords | Validadores Django (longitud, complejidad mínima acordada) |
| JWT en logs | Nunca loguear token completo |
| gRPC interno | Red Docker privada; sin exponer 50051 públicamente sin TLS si el cloud lo expone |
| Enumeración | `forgot-password` respuesta uniforme |

---

## 7. Matriz de pruebas obligatorias

| ID | Caso | Esperado |
|----|------|------------|
| T1 | Login admin | 200 + tokens + rol admin |
| T2 | `me` sin header | 401 |
| T3 | Refresh válido | Nuevo access |
| T4 | Logout + refresh reuse | 401 |
| T5 | Forgot email existente | Correo recibido (MS-6) |
| T6 | Reset token válido | Password cambia |
| T7 | Reset token reusado | 400 |
| T8 | `ValidateToken` gRPC token inválido | `valid=false` o error según implementación |
| T9 | `CreateUser` duplicado | `success=false` |
| T10 | Alumno accede `GET /usuarios` | 403 |

---

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Reloj desincronizado JWT | NTP en contenedores; `LEEWAY` simplejwt si hace falta |
| MS-6 caído | Forgot-password: encolar reintento o error 503 controlado sin revelar existencia |
| Rotación de SECRET_KEY | Documentar que invalida todos los JWT previos |
| API key filtrada | Rotación + nunca en Git |

---

## 9. Checklist de salida Epic 3

- [ ] ISSUE-301 … 308 completados.  
- [ ] `proto/auth.proto` alineado con implementación (incl. `CreateUser`).  
- [ ] Postman: carpeta Auth con flujos login → me → logout → refresh fallido.  
- [ ] Manual técnico: cómo otros MS validan JWT (Epic 11).  
- [ ] Sin secretos en repositorio (ISSUE-1106).  

---

## 10. Referencias

- `docs/backlog_AGM_completo.md` — Epic 3  
- `docs/Proyecto_Final_SW_AGM.md` — §5.3 Módulo 1, §5.4.1  
- `docs/microservicios/MS1_AUTH_USERS.md`  
- `proto/auth.proto`  
