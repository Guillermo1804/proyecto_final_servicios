# Plan de acción — MS-2 Periodos & Materias (Epic 4)

**Desarrollador:** Alane  
**Microservicio:** MS-2 — Periodos & Materias  
**Carpeta:** `/ms-periodos/`  
**REST:** `8002` · **gRPC:** `50052` · **BD:** MySQL `agm_periodos_db`  
**Backlog:** `docs/backlog_AGM_completo.md` — **Epic 4 (ISSUE-401 … ISSUE-408)**  
**Enunciado:** `docs/Proyecto_Final_SW_AGM.md` — §5.2.1 Admin (periodos, import PDF materias), §5.3 Módulos 2 y 3, §5.4.1 MS-2  
**Contexto:** `docs/CONTEXTO_GLOBAL_PROYECTO.md` — §4, §5 (MS-2 llamadas)  
**Especificación:** `docs/microservicios/MS2_PERIODOS_MATERIAS.md`  
**Contrato:** `proto/periodos.proto`

---

## 1. Rol del MS-2

MS-2 gobierna el **calendario académico** y el **catálogo de materias** por periodo:

- CRUD de **periodos** con regla **exactamente un periodo activo** en todo el sistema.  
- **Importación masiva** de materias desde PDF oficial (parsing tolerante a fallos parciales).  
- CRUD de **materias** (NRC, clave, sección, docente asignado, horario).  
- **gRPC** para que MS-3, MS-4, MS-6 y MS-7 obtengan `Materia`, listado por docente y **periodo activo**.  
- Validación **JWT + rol** vía MS-1 en todos los endpoints que lo requieran.

**No hace:** almacenar alumnos inscritos (MS-3); calificaciones (MS-4).

---

## 2. Resultados medibles (“terminado”)

| # | Resultado | Evidencia |
|---|------------|-----------|
| P1 | Modelos `Periodo`, `Materia` + migraciones | `agm_periodos_db` con constraints |
| P2 | Un solo `activo=True` | Constraint parcial MySQL + transacción en activar |
| P3 | Import PDF | Resumen `importadas` / `fallidas` con motivos |
| P4 | gRPC `PeriodosService` | 3 RPC según `periodos.proto` en **50052** |
| P5 | JWT en REST | Sin Bearer → 401 |
| P6 | `GET /periodos/activo` | 200 o 404 coherente |
| P7 | Listados paginados + búsqueda | Formato estándar §5.4.5 / `CONTEXTO_GLOBAL` §6.1 |

---

## 3. Alineación de rutas: backlog vs spec MS2

| Funcionalidad | Backlog (ISSUE-403) | Spec MS2 | Acción recomendada |
|---------------|---------------------|-----------|---------------------|
| Importar materias | `POST /periodos/importar` + periodo destino en body/query | `POST /periodos/:id/importar` | **Unificar** en el código y documentar en Postman la ruta final; el periodo destino debe quedar inequívoco |

---

## 4. Dependencia MS-3 / Epic 2 — `GetDocenteByNombre`

El **ISSUE-403** del backlog menciona gRPC `GetDocenteByNombre` en MS-3. En `proto/alumnos.proto` actual figura **`GetDocenteByUsuarioId`**, no búsqueda por nombre.

| Opción | Descripción |
|--------|-------------|
| A | Añadir RPC `GetDocenteByNombre` / `ResolveDocenteByNombre` en `alumnos.proto` (Epic 2) e implementarlo en MS-3 |
| B | Tras importar PDF, dejar solo `docente_nombre` en MS-2 y rellenar `docente_id` en un job manual o al sincronizar catálogo docentes |

**Plan robusto:** documentar la decisión en el Manual Técnico; no dejar el import “colgado” sin criterio.

---

## 5. Clientes gRPC salientes (MS-2 → otros)

| Destino | Método | Uso |
|---------|--------|-----|
| MS-1 | `ValidateToken` | Cada request autenticado |
| MS-1 | `CheckRole` | Escrituras solo `admin` |
| MS-3 | `GetAlumnosByMateria` | Antes de `DELETE /materias/:id` (no borrar si hay inscritos activos) |

**Timeouts y errores:** mapear `DEADLINE_EXCEEDED` a 503 con mensaje claro si MS-1 o MS-3 no responden.

---

## 6. Plan por issue (granular)

### ISSUE-401 — Base Django MS-2

| # | Tarea | Criterio |
|---|--------|----------|
| 401.1 | Proyecto en `/ms-periodos/`, Django 5 + DRF | `migrate` OK |
| 401.2 | `pdfplumber` (+ `pdfminer.six` si aplica) | Parsing import |
| 401.3 | MySQL `agm_periodos_db`, `utf8mb4` | |
| 401.4 | Modelos `Periodo`, `Materia` | FK periodo→materias; `unique_together` (periodo, nrc) |
| 401.5 | Constraint periodo activo único | `UniqueConstraint` condicional `activo=True` (ver MS2 doc) |
| 401.6 | Dockerfile / gunicorn | Puerto 8002 |

---

### ISSUE-402 — CRUD periodos

| # | Tarea | Criterio |
|---|--------|----------|
| 402.1 | `GET /periodos` | Paginación |
| 402.2 | `POST /periodos` | Solo admin; `fecha_inicio < fecha_fin` |
| 402.3 | `PUT /periodos/:id` | |
| 402.4 | `DELETE /periodos/:id` | Solo sin materias |
| 402.5 | `POST /periodos/:id/activar` | **Transacción:** desactivar otros, activar este |
| 402.6 | Concurrencia | Dos activaciones simultáneas no dejan dos activos (bloqueo DB o `select_for_update`) |

---

### ISSUE-403 — Importación PDF materias

| # | Tarea | Criterio |
|---|--------|----------|
| 403.1 | Multipart PDF + `periodo_id` | Validar que el periodo exista |
| 403.2 | Parser por páginas/tablas | Ajustar a PDF real BUAP (iterar con muestras reales) |
| 403.3 | Normalización | Strip, encoding UTF-8, NRC vacío → fila fallida |
| 403.4 | Upsert por NRC dentro del periodo | No duplicar filas |
| 403.5 | Resumen estructurado | `success`, `data` con conteos y `errores[]` |
| 403.6 | PDF corrupto / no tabla | 400 con mensaje |

**Pruebas:** PDF mínimo de prueba en repo (solo si licencia lo permite) o captura en manual; nunca PDF con datos personales reales sin anonimizar.

---

### ISSUE-404 — CRUD materias

| # | Tarea | Criterio |
|---|--------|----------|
| 404.1 | `GET /materias?periodo=:id` | Paginación + `search` NRC/nombre |
| 404.2 | `GET /materias/:id` | |
| 404.3 | `PUT /materias/:id` | Admin |
| 404.4 | `DELETE /materias/:id` | Llamar MS-3; si hay alumnos → 400 |

---

### ISSUE-405 — Servidor gRPC (50052)

| # | Tarea | Criterio |
|---|--------|----------|
| 405.1 | `GetMateriaById` | `NOT_FOUND` si no existe |
| 405.2 | `GetMateriasByDocente` | Filtrar por `docente_id` en modelo; vacío si ninguna |
| 405.3 | `GetPeriodoActivo` | `Empty` request; error claro si no hay activo |
| 405.4 | Paridad con `periodos.proto` | Stubs regenerados |

---

### ISSUE-406 — Validación JWT

| # | Tarea | Criterio |
|---|--------|----------|
| 406.1 | Decorador `grpc_jwt_required` | Extrae `Authorization: Bearer` |
| 406.2 | Llama `ValidateToken` MS-1 | Inyecta `request.user_id` / claims en vista |
| 406.3 | Aplicar a rutas protegidas | Lista explícita en código o mixin DRF |

**Excepciones:** `GET /periodos/activo` según ISSUE-407 (público o cualquier rol autenticado — acordar con equipo).

---

### ISSUE-407 — Periodo activo

| # | Tarea | Criterio |
|---|--------|----------|
| 407.1 | `GET /periodos/activo` | 404 si ningún periodo `activo=True` |
| 407.2 | Política de auth | Documentar si es público o requiere JWT |

---

### ISSUE-408 — Paginación y búsqueda

| # | Tarea | Criterio |
|---|--------|----------|
| 408.1 | `?page=&limit=` en periodos y materias | Default sensato (p. ej. page=1, limit=10) |
| 408.2 | Envelope `{ success, data, pagination: { page, total } }` | Alineado proyecto |

---

## 7. Seguridad

| Tema | Regla |
|------|--------|
| Admin | Nunca confiar solo en el JWT del cliente sin validar con MS-1 |
| PDF upload | Límite de tamaño; MIME `application/pdf`; antivirus opcional |
| Rate limit | Opcional en import para evitar DoS |

---

## 8. Matriz de pruebas

| ID | Caso | Esperado |
|----|------|------------|
| T1 | Activar periodo B con A activo | Solo B activo |
| T2 | Activar dos veces en paralelo | Un solo activo |
| T3 | Import PDF válido | Materias creadas + resumen |
| T4 | Delete materia con alumnos | 400 |
| T5 | gRPC `GetPeriodoActivo` sin activo | Comportamiento definido (error o vacío) |
| T6 | JWT inválido en POST periodo | 401 |

---

## 9. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| PDF BUAP cambia layout | Parser versionado + pruebas con fixture |
| Reloj y fechas | Timezone `America/Mexico_City` o UTC documentado |
| MS-3 caído al delete materia | 503 o reintento con mensaje |

---

## 10. Checklist salida Epic 4

- [ ] ISSUE-401 … 408 completados.  
- [ ] `proto/periodos.proto` implementado.  
- [ ] Postman: periodos + import + materias + gRPC (grpcurl).  
- [ ] README / manual: ruta final de importación PDF.  

---

## 11. Referencias

- `docs/backlog_AGM_completo.md` — Epic 4  
- `docs/Proyecto_Final_SW_AGM.md` — §5.2.1, §5.3 módulos 2–3  
- `docs/microservicios/MS2_PERIODOS_MATERIAS.md`  
- `proto/periodos.proto`  
