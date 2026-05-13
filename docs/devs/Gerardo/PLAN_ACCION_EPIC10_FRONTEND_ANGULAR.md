# Plan de acción — Frontend Angular 20 (Epic 10 — Punto extra)

**Desarrollador:** Gerardo  
**Alcance:** `docs/backlog_AGM_completo.md` — **Epic 10 (ISSUE-1001 … ISSUE-1012)**  
**Enunciado:** `docs/Proyecto_Final_SW_AGM.md` — **§5.5** (Angular 20 SPA, JWT, lazy loading, guards, interceptors, reactive forms, QR, diseño, criterio de punto extra §5.5.3)  
**Contexto:** `docs/CONTEXTO_GLOBAL_PROYECTO.md` — §2 (cliente → gateway HTTPS), rutas `/auth/*`, `/periodos/*`, etc.

> **Advertencia:** el frontend es **opcional** para aprobar el proyecto base (backend). El **+1 punto** solo aplica si está **100% completo**, conectado al **backend en producción** y con **diseño profesional** (§5.5.3). Un frontend parcial o con mocks **no** otorga el extra.

---

## 1. Objetivo del plan

Entregar una **SPA Angular 20** que consuma los microservicios **reales** desplegados (idealmente vía **API Gateway** Nginx con una `apiUrl` base), con:

- Autenticación JWT en todas las peticiones.  
- Módulos por rol (**Admin**, **Docente**, **Alumno**) con **lazy loading**.  
- **Guards** y **interceptors** según enunciado.  
- **Reactive Forms** con validación visual.  
- **QR dinámico** (alumno) y **escaneo con cámara** (docente).  
- **UX mobile-first** y librería de componentes (Material / PrimeNG / Taiga / ng-zorro).  
- **Sin** Bootstrap genérico sin personalizar; **sin** tablas HTML “desnudas”.

---

## 2. Resultados medibles (criterio “punto extra”)

| # | Resultado | Evidencia |
|---|-------------|-----------|
| F1 | Proyecto Angular 20 en `/frontend` (o ruta acordada) | `ng build --configuration production` sin errores |
| F2 | `environment*.ts` | Todas las URLs desde env; **cero** hardcode de prod en código |
| F3 | Lazy modules Admin / Docente / Alumno | Rutas cargan chunk al navegar |
| F4 | Interceptor JWT + 401 → login | Prueba en red: ver `Authorization: Bearer` |
| F5 | Guards por rol | Alumno no entra a `/admin` |
| F6 | Todos los flujos del enunciado §6.3 video | Admin, docente, alumno, QR, reportes |
| F7 | HTTPS + CORS | App en Vercel/Netlify/Pages sin errores CORS contra APIs prod |

---

## 3. Arquitectura HTTP recomendada

| Opción | Descripción | Pros |
|--------|-------------|------|
| A | Una sola `environment.apiBaseUrl` al **Nginx** gateway | Un solo origen CORS; paths `/auth`, `/periodos`, … |
| B | Variables por MS (`apiAuth`, `apiPeriodos`, …) | Útil si no hay gateway en prod |

**Alineación:** `CONTEXTO_GLOBAL_PROYECTO.md` recomienda Nginx; el frontend debería preferir **Opción A** y construir URLs relativas (`${apiBase}/auth/login`).

**Servicios Angular:** un `AuthApiService` contra MS-1; `PeriodosApiService`, etc., o un `HttpClient` genérico con prefijos por dominio.

---

## 4. Mapa backlog ↔ módulos UI

| ISSUE | Entregable UI | Rol |
|-------|----------------|-----|
| 1001 | Shell app, routing, Material, interceptors, guards, `AuthService`, environments | Transversal |
| 1002 | Login, Forgot, Reset password | Público |
| 1003 | Dashboard admin, periodos, PDF materias/docentes, tabla docentes | Admin |
| 1004 | Dashboard docente + gráficas + tabla resumen materias | Docente |
| 1005 | Materias, alumnos, ponderaciones, actividades, calificaciones, cerrar materia | Docente |
| 1006 | Sesión 10 min, temporizador, escáner QR, lista en vivo, cerrar sesión | Docente |
| 1007 | Dashboard alumno, materias, detalle, baja, estadísticas asistencia | Alumno |
| 1008 | QR regenerable ~30 s, `angularx-qrcode`, temporizador | Alumno |
| 1009 | Export Excel/PDF concentrado (MS-7), descarga `blob` | Docente |
| 1010 | Responsive, tablas Material con sort/filter/page, formularios con errores/spinners/toasts | Transversal |
| 1011 | Build prod + deploy estático + `environment.prod.ts` | DevOps frontend |
| 1012 | Historial docente comparativo por periodos | Docente |

---

## 5. Plan por issue (granular)

### ISSUE-1001 — Configuración base Angular

| # | Tarea | Criterio |
|---|--------|----------|
| 1001.1 | `ng new` con routing y SCSS | Estructura limpia |
| 1001.2 | UI library (`ng add @angular/material` u otra aprobada §5.5.2) | Tema único (paleta tipografía) |
| 1001.3 | `environment.ts` / `environment.prod.ts` | `apiBaseUrl`, opcional `frontendUrl` para links en emails |
| 1001.4 | Lazy routes `loadChildren` | `admin`, `docente`, `alumno` |
| 1001.5 | Interceptor **JWT** | Lee token de `sessionStorage`/`localStorage` (acordar); añade `Authorization: Bearer` |
| 1001.6 | Interceptor **401** | Limpia sesión, navega a `/login` sin bucle infinito |
| 1001.7 | `CanActivate` por rol | Lee claims del JWT (decode seguro del payload **o** `/auth/me` al iniciar) |
| 1001.8 | `AuthService` | `login()`, `logout()`, `refreshToken()`, `getCurrentUser()`, `isRole()` |

**Errores frecuentes:** guard que dispara petición sin token → 401 → loop; excluir rutas públicas del interceptor de anexar token si aplica.

---

### ISSUE-1002 — Módulo autenticación (público)

| # | Tarea | Criterio |
|---|--------|----------|
| 1002.1 | Login `FormGroup` | Validators: email, required password; `markAllAsTouched` en submit |
| 1002.2 | Spinner + mensaje error servidor | 401 mostrado en UI |
| 1002.3 | Forgot password | Async: POST forgot; mensaje genérico de éxito (no revelar si existe email) |
| 1002.4 | Reset password | Leer `token` de `ActivatedRoute` query params; POST reset |
| 1002.5 | Post-login redirect | `admin` → `/admin`; `docente` → `/docente`; `alumno` → `/alumno` |

**Reactive forms “asíncronos”:** validación async opcional (p. ej. comprobar email disponible solo si hubiera registro público; en AGM basta documentar validación async donde tenga sentido, ej. preview import).

---

### ISSUE-1003 — Administrador

| # | Tarea | Criterio |
|---|--------|----------|
| 1003.1 | Dashboard: periodo activo (`GET /periodos/activo`), fecha/hora cliente o servidor | Datos reales |
| 1003.2 | CRUD periodos | Tabla paginada, crear/editar, activar (confirmación) |
| 1003.3 | Import PDF materias | `multipart/form-data`; barra progreso `HttpEventType.UploadProgress` |
| 1003.4 | Import PDF docentes | Igual |
| 1003.5 | Tabla docentes + búsqueda + reset password | Llamadas reales MS-3 / MS-1 según API |

---

### ISSUE-1004 — Dashboard docente

| # | Tarea | Criterio |
|---|--------|----------|
| 1004.1 | KPIs: materias asignadas, alumnos totales | Agregación desde APIs reales (MS-2 + MS-3 o endpoints agregados) |
| 1004.2 | % asistencia del día | MS-5 `.../hoy` o estadísticas docente según contrato |
| 1004.3 | Gráficas Chart.js / Apex / ng2-charts | Al menos una serie por KPI |
| 1004.4 | Tabla resumen materias | Columnas: NRC, nombre, estado |

---

### ISSUE-1005 — Materias docente

| # | Tarea | Criterio |
|---|--------|----------|
| 1005.1 | Lista materias periodo activo | MS-2 |
| 1005.2 | Detalle: tabs o secciones alumnos, ponderaciones, actividades, concentrado | MS-3, MS-4 |
| 1005.3 | Import alumnos Excel | **Vista previa** antes de confirmar (dos pasos) |
| 1005.4 | Ponderaciones | UI suma 100% en vivo + error si ≠100 |
| 1005.5 | CRUD actividades | |
| 1005.6 | Calificaciones | Celda editable + import Excel |
| 1005.7 | Cerrar materia | Modal confirmación; POST cierre MS-4 |

---

### ISSUE-1006 — Asistencias QR docente

| # | Tarea | Criterio |
|---|--------|----------|
| 1006.1 | Iniciar sesión | `POST /sesiones/iniciar`; guardar `sesion_id` |
| 1006.2 | Temporizador 10:00 → 0:00 | `interval` + `takeWhile` o similar |
| 1006.3 | Cámara + jsQR / zxing | `getUserMedia`; manejo permisos denegados |
| 1006.4 | Enviar payload escaneado | `POST /asistencias/registrar` |
| 1006.5 | Lista en vivo | Polling `stats` o refresh tras cada éxito |
| 1006.6 | Cerrar sesión anticipada | `DELETE` sesión |
| 1006.7 | Prueba en Chrome Android | Layout táctil usable |

---

### ISSUE-1007 — Módulo alumno

| # | Tarea | Criterio |
|---|--------|----------|
| 1007.1 | Dashboard datos perfil | Desde `/auth/me` + MS-3 si hace falta |
| 1007.2 | Lista materias | |
| 1007.3 | Detalle calificaciones | MS-4 concentrado o vista alumno |
| 1007.4 | Baja materia | Modal irreversible; `DELETE` baja |
| 1007.5 | Estadísticas asistencia | MS-5 o MS-7 según API |

---

### ISSUE-1008 — QR dinámico alumno

| # | Tarea | Criterio |
|---|--------|----------|
| 1008.1 | `GET /qr/generate` cada 30 s | `interval(30000)` + `switchMap` |
| 1008.2 | `angularx-qrcode` | Tamaño legible en móvil |
| 1008.3 | Countdown visual “próxima renovación” | |
| 1008.4 | Selección de materia si el alumno tiene varias | Query `materia_id` |

---

### ISSUE-1009 — Reportes (blob)

| # | Tarea | Criterio |
|---|--------|----------|
| 1009.1 | Botones exportar | `responseType: 'blob'` |
| 1009.2 | Descarga | `URL.createObjectURL` + `<a download>` |
| 1009.3 | Nombre archivo | Desde header `Content-Disposition` si existe |

---

### ISSUE-1010 — UX global

| # | Tarea | Criterio |
|---|--------|----------|
| 1010.1 | Layout responsive | Breakpoints Material |
| 1010.2 | Sidebar / toolbar | Menú hamburguesa móvil |
| 1010.3 | `MatTableDataSource` o equivalente | Paginación, filter, sort |
| 1010.4 | Feedback | Snackbar / toast errores y éxitos |
| 1010.5 | Tema SCSS** | Variables de color del equipo |

---

### ISSUE-1011 — Despliegue

| # | Tarea | Criterio |
|---|--------|----------|
| 1011.1 | `ng build --configuration production` | `outputHashing` optimizado |
| 1011.2 | Deploy Vercel/Netlify/GitHub Pages | URL HTTPS pública |
| 1011.3 | `environment.prod.ts` | URLs **producción** reales del backend |
| 1011.4 | CORS | Origen del frontend en `CORS_ALLOWED_ORIGINS` de cada MS o del gateway |

---

### ISSUE-1012 — Historial docente

| # | Tarea | Criterio |
|---|--------|----------|
| 1012.1 | Vista periodos + materias | `GET /estadisticas/docente/:id` MS-7 |
| 1012.2 | Gráfica comparativa misma materia multi-periodo | |
| 1012.3 | Badges periodo inactivo | Datos desde MS-2 si expone flag |

---

## 6. Seguridad en el cliente

| Tema | Regla |
|------|--------|
| Tokens | No exponer en URL salvo reset token controlado; preferir `sessionStorage` para access si se desea mitigar XSS persistente |
| XSS | Evitar `innerHTML` con datos usuario |
| HTTPS | Obligatorio en prod (§5.4.6) |
| Logout | Llamar `POST /auth/logout` y borrar tokens locales |

---

## 7. Matriz de pruebas E2E (manual o Cypress)

| ID | Flujo |
|----|--------|
| E1 | Admin: login → crear periodo → importar PDF (archivo pequeño de prueba) |
| E2 | Docente: ponderaciones 100% → actividad → calificación → concentrado |
| E3 | Docente: iniciar sesión asistencia → escanear QR alumno → ver presente/retardo |
| E4 | Alumno: ver materias → QR rota cada 30s |
| E5 | Alumno: solicitar baja → confirmar |
| E6 | Export PDF/XLS desde concentrado |
| E7 | 401: token borrado → redirige login |

---

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| CORS en prod | Resolver **antes** de la entrega; lista explícita de orígenes |
| Gateway path distinto | Centralizar constantes de path en `api.routes.ts` |
| Cámara no HTTPS | getUserMedia requiere contexto seguro; probar en prod |
| Alcance gigante | Orden sugerido: 1001→1002→1003→1004→1005→1008→1006→1007→1009→1012→1010→1011 |

---

## 9. Checklist de salida Epic 10 (punto extra)

- [ ] Todos los ISSUE-1001 … 1012 cubiertos en código.  
- [ ] **Sin mocks** en flujos principales (§5.5.3).  
- [ ] Diseño coherente (no “Bootstrap por defecto”).  
- [ ] Video §6.3 muestra frontend en móvil si aplica.  
- [ ] README con URL del frontend en producción.  

---

## 10. Referencias

- `docs/backlog_AGM_completo.md` — Epic 10  
- `docs/Proyecto_Final_SW_AGM.md` — §5.5, §7.1 punto extra  
- `docs/CONTEXTO_GLOBAL_PROYECTO.md` — gateway y rutas  
