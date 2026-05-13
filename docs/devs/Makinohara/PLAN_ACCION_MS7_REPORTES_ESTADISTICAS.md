# Plan de acción — MS-7 Reportes y Estadísticas (Epic 9)

**Desarrollador:** Makinohara  
**Microservicio:** MS-7 — Reportes & Estadísticas  
**Carpeta:** `/ms-reportes/`  
**REST:** `8007` · **gRPC:** `50057` · **BD:** MySQL `agm_reportes_db`  
**Backlog:** `docs/backlog_AGM_completo.md` — **ISSUE-901 … ISSUE-907**  
**Enunciado:** `docs/Proyecto_Final_SW_AGM.md` — §5.2.2 (exportación Excel/PDF), §5.2.2 y §5.2.3 (historial/estadísticas), §5.3 **Módulos 8 y 9**, §5.4.1 fila MS-7  
**Contexto:** `docs/CONTEXTO_GLOBAL_PROYECTO.md` §4–§5  
**Especificación:** `docs/microservicios/MS7_REPORTES_ESTADISTICAS.md`  
**Contrato:** `proto/reportes.proto`

---

## 1. Rol del MS-7 en el sistema AGM

MS-7 **no** es la fuente de verdad de calificaciones ni asistencias. Su función es:

1. **Agregar** datos vía **gRPC** desde MS-2, MS-3, MS-4 y MS-5.  
2. **Generar archivos** (Excel `openpyxl`, PDF `reportlab` u otra librería acordada) para **actas** y archivo institucional.  
3. **Exponer JSON** de estadísticas para docente (historial comparativo) y alumno (dashboard académico).  
4. **Exponer gRPC** `GenerateReport` y `GetHistorialDocente` según `reportes.proto`.

**Regla de arquitectura:** no leer `agm_calificaciones_db` ni otras BDs ajenas; solo `agm_reportes_db` para metadatos/caché opcional.

---

## 2. Contrato gRPC oficial (`reportes.proto`)

| RPC | Request | Response | Uso típico |
|-----|---------|----------|------------|
| `GenerateReport` | `tipo` (`calificaciones` \| `asistencias`), `materia_id`, `formato` (`pdf` \| `xlsx`) | `success`, `archivo` (bytes), `filename`, `content_type` | Otros MS o jobs batch (opcional) |
| `GetHistorialDocente` | `docente_id` | `HistorialDocenteResponse` con `repeated StatsPeriodo` | Frontend historial / ISSUE-1012 |

### `StatsPeriodo` (campos del proto)

`periodo_nombre`, `periodo_id`, `materia_nombre`, `materia_id`, `total_alumnos`, `aprobados`, `reprobados`, `promedio_grupal`, `porcentaje_asistencia`.

La implementación debe **rellenar** estos campos con las mismas reglas de negocio que los endpoints REST (consistencia REST ↔ gRPC).

---

## 3. Endpoints REST (backlog + gateway)

Prefijo Nginx: `/reportes/*` y `/estadisticas/*` → puerto **8007** (ver `CONTEXTO_GLOBAL_PROYECTO.md` §2).

### 3.1 Reportes (ISSUE-902, 903, 904)

| GET | Parámetros | Origen datos | ISSUE |
|-----|------------|--------------|-------|
| `/reportes/calificaciones/:materiaId` | `formato`: aceptar **`xls`**, **`xlsx`** y/o **`pdf`** (unificar con gateway y proto: proto usa `xlsx`) | MS-4 `GetConcentrado`, MS-3 alumnos, MS-2 materia | 902–903 |
| `/reportes/asistencias/:materiaId` | `formato=pdf` \| `xls` \| `xlsx` | MS-5 `GetEstadisticasAsistencia`, MS-3 nombres | 904 |

**Headers de respuesta binaria:**

- `Content-Type`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` o `application/pdf`  
- `Content-Disposition`: `attachment; filename="calificaciones_<NRC>.xlsx"` (nombre derivado de MS-2 si está disponible)

**Errores HTTP:** 400 formato inválido; 401 sin JWT; 403 si el usuario no es docente de esa materia ni admin; 404 materia o datos no encontrados; 502/504 si gRPC upstream falla por timeout (definir política: preferir 503 con mensaje claro).

---

### 3.2 Estadísticas (ISSUE-905, 906)

| GET | Descripción | ISSUE |
|-----|-------------|-------|
| `/estadisticas/docente/:id` | `id` = identificador acordado (**usuario_id** docente vs `docente_id` de tabla MS-3 — **definir y documentar** en OpenAPI) | 905 |
| `/estadisticas/alumno/:id` | Mismas reglas de identificador; alumno solo puede ver **su** `id` | 906 |

**Enunciado §5.2.2:** historial con comparativa entre periodos si la misma materia se impartió varias veces → la respuesta debe permitir agrupar por `materia_id` o nombre normalizado y listar periodos.

---

## 4. Mapa de llamadas gRPC (MS-7 → otros)

| Cuándo | MS destino | Métodos |
|--------|------------|---------|
| Validar petición | MS-1 | `ValidateToken` (+ `CheckRole` si aplica) |
| Encabezados de reportes y estadísticas docente | MS-2 | `GetMateriaById`, `GetMateriasByDocente`, `GetPeriodoActivo` (si hace falta) |
| Nombres y matrículas | MS-3 | `GetAlumnosByMateria`, datos por alumno |
| Concentrado y stats de calificaciones | MS-4 | `GetConcentrado`, `GetEstadisticasMateria`, `GetPromedioAlumno` |
| Asistencias | MS-5 | `GetEstadisticasAsistencia`, `GetAsistenciaAlumno` |

**Timeouts:** configurar por destino (MS-4 con muchas actividades puede ser más lento). Evitar N+1 sin límite: si el equipo agrega batch RPC en el futuro, documentar.

---

## 5. Reglas de negocio que no puede romper MS-7

| Regla | Fuente | Implementación |
|-------|--------|----------------|
| Promedio **real** y **redondeado** (≥0.5 arriba) | Enunciado §5.2.2, ISSUE-606 | Copiar exactamente los valores que devuelve MS-4 en `GetConcentrado`; no recalcular en MS-7 salvo prueba cruzada |
| Solo docente titular o admin descarga reportes | RBAC | Tras `ValidateToken`, comprobar que `docente_id` de la materia (MS-2) coincide con el usuario |
| Charset nombres BUAP | Seeds / datos reales | UTF-8 en Excel y PDF |

---

## 6. Diseño de archivos generados

### 6.1 Excel calificaciones (ISSUE-902)

| Sección | Contenido |
|---------|-----------|
| Fila 1–3 | Institución, nombre materia, NRC, sección, periodo, docente (desde MS-2) |
| Cabecera tabla | Matrícula, nombre, [una columna por actividad o por categoría según contrato MS-4], promedio real, promedio redondeado |
| Filas | Un alumno por fila; orden estable (p. ej. por matrícula) |
| Ancho columnas | Autoajuste básico para legibilidad |

### 6.2 PDF calificaciones (ISSUE-903)

- Misma información que Excel en layout tabular.  
- Pie de página: fecha de generación, usuario que generó (opcional).  
- Logo BUAP: opcional según backlog.

### 6.3 Excel/PDF asistencias (ISSUE-904)

Columnas mínimas: alumno (nombre, matrícula), total clases, presentes, retardos, ausentes, % asistencia.  
Fuente: MS-5 + cruce con lista de inscritos MS-3 para alumnos sin registro (ausentes acumulados según regla acordada con MS-5).

---

## 7. Plan por issue (granular)

### ISSUE-901 — Configuración base Django (MS-7)

| # | Tarea | Criterio |
|---|--------|----------|
| 901.1 | Proyecto en `/ms-reportes/`, Django 5 + DRF | `check` OK |
| 901.2 | MySQL `agm_reportes_db` | Migraciones |
| 901.3 | Dependencias: `openpyxl`, `reportlab`, `grpcio`, `grpcio-tools` | Versiones fijadas |
| 901.4 | (Opcional) modelo `ReporteGenerado` para caché | Solo si el equipo lo necesita |
| 901.5 | `generate_proto.sh` y stubs MS-1,2,3,4,5 | Compilación reproducible |
| 901.6 | Dockerfile / entrypoint | Paridad con otros MS |

---

### ISSUE-902 — Reporte calificaciones Excel

| # | Tarea | Criterio |
|---|--------|----------|
| 902.1 | Vista GET con `materiaId` path y `formato` query | Validar enum |
| 902.2 | Llamar `GetConcentrado(materia_id)` | Manejar lista vacía |
| 902.3 | Llamar MS-3 para nombres | Join por `alumno_id` |
| 902.4 | Llamar MS-2 para metadata materia | NRC en filename |
| 902.5 | Generar workbook `openpyxl` | Abre sin error en Excel/LibreOffice |
| 902.6 | Respuesta archivo | Sin JSON envolviendo el binario en el mismo response (es descarga directa) — **o** si el API estándar del equipo exige JSON base64, documentar excepción |

**Nota:** backlog menciona `formato=xls`; XLS real es formato legacy. Lo habitual es **xlsx** (`openpyxl`). Alinear query param con frontend y Postman.

---

### ISSUE-903 — Reporte calificaciones PDF

| # | Tarea | Criterio |
|---|--------|----------|
| 903.1 | Reutilizar capa de “datos del reporte” de 902 | Misma tabla de datos |
| 903.2 | `reportlab` Platypus (SimpleDocTable) o equivalente | Paginación si muchas filas |
| 903.3 | Fuentes que soporten UTF-8 | Acentos correctos |

---

### ISSUE-904 — Reporte asistencias

| # | Tarea | Criterio |
|---|--------|----------|
| 904.1 | GET `/reportes/asistencias/:materiaId` | Mismos `formato` que calificaciones |
| 904.2 | `GetEstadisticasAsistencia` | Contrato con MS-5 verificado |
| 904.3 | Merge con alumnos MS-3 | Filas completas para todos los inscritos activos |

---

### ISSUE-905 — Estadísticas docente

| # | Tarea | Criterio |
|---|--------|----------|
| 905.1 | `GetMateriasByDocente(docente_id)` | Lista materias por periodo |
| 905.2 | Por cada materia: `GetEstadisticasMateria` (MS-4) | Promedio grupal, aprobados/reprobados |
| 905.3 | Asistencia: `GetEstadisticasAsistencia` (MS-5) por materia | % en `StatsPeriodo` coherente |
| 905.4 | Comparativa multi-periodo | Agrupar por nombre de materia o `clave` normalizada; indicar periodo activo vs finalizado (flags desde MS-2 si existen) |
| 905.5 | JSON estándar `{ success, data, message }` | Paginación si la lista crece |

**Performance:** cache en memoria corta o tabla en `agm_reportes_db` solo si las demos son lentas; documentar en manual técnico.

---

### ISSUE-906 — Estadísticas alumno

| # | Tarea | Criterio |
|---|--------|----------|
| 906.1 | Resolver materias inscritas del alumno | vía MS-3 (endpoints o gRPC existentes) |
| 906.2 | Por materia: `GetPromedioAlumno` (MS-4) | |
| 906.3 | Por materia: `GetAsistenciaAlumno` (MS-5) | |
| 906.4 | Campos: promedio actual, % asistencia, activas vs históricas | Alineado enunciado §5.2.3 |
| 906.5 | Autorización estricta | Token alumno solo `alumno_id == self` |

---

### ISSUE-907 — Servidor gRPC

| # | Tarea | Criterio |
|---|--------|----------|
| 907.1 | `GenerateReport` | Misma lógica que REST de descarga (bytes + filename + content_type) |
| 907.2 | `GetHistorialDocente` | Misma lógica que `GET /estadisticas/docente/:id` |
| 907.3 | Puerto **50057** | Sin colisiones |
| 907.4 | Errores gRPC | `NOT_FOUND`, `PERMISSION_DENIED`, `INTERNAL` con mensajes seguros |

---

## 8. Autorización (matriz recomendada)

| Recurso | Admin | Docente | Alumno |
|---------|-------|---------|--------|
| Reporte calif. materia M | Sí | Sí si es su materia | No |
| Reporte asist. materia M | Sí | Sí si es su materia | No |
| Estadísticas docente D | Sí | Sí si `D` es su propio id | No |
| Estadísticas alumno A | Sí (solo si política lo permite) | No | Sí si `A` es su propio id |

---

## 9. Matriz de pruebas

| ID | Caso | Pasos | Esperado |
|----|------|-------|----------|
| R1 | Excel calificaciones | Materia con 3 alumnos, actividades varias | Archivo abre, números = MS-4 UI/API |
| R2 | PDF calificaciones | Igual | PDF legible, UTF-8 |
| R3 | Excel asistencias | Materia con sesiones en MS-5 | % coherente |
| R4 | Stats docente | Docente con 2 periodos misma materia | Bloque comparativo en JSON |
| R5 | Stats alumno | Token alumno | 200 solo para su id; 403 para otro id |
| R6 | Formato mal | `formato=doc` | 400 |
| R7 | gRPC `GenerateReport` | Cliente de prueba | `success=true`, bytes no vacíos |

---

## 10. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| MS-4 timeout en materias grandes | Timeout configurable; mensaje 503; considerar paginación en MS-4 |
| Inconsistencia `xls` vs `xlsx` | Tabla de alias en vista: aceptar ambos query strings |
| Memoria con PDF grandes | Streaming o generación en archivo temporal + `FileResponse` |
| IDs docente/alumno ambiguos | Documentar en README y Postman qué `id` es (usuario vs entidad) |

---

## 11. Checklist de salida Epic 9

- [ ] ISSUE-901 … 907 implementados y enlazados en backlog.  
- [ ] Endpoints probados detrás de **Nginx** con el mismo path que en prod.  
- [ ] Postman: descarga binaria (guardar ejemplo `.xlsx` en repo solo si el equipo lo permite; mejor captura en manual).  
- [ ] Enunciado §6.3 video: exportación Excel/PDF en flujo docente.  
- [ ] `proto/reportes.proto` y servidor **50057** verificados con `grpcurl`.  

---

## 12. Referencias

- `docs/backlog_AGM_completo.md` — Epic 9  
- `docs/Proyecto_Final_SW_AGM.md` — Módulos 8 y 9, tabla MS-7 §5.4.1  
- `docs/CONTEXTO_GLOBAL_PROYECTO.md` — §5 (MS-7 llamadas)  
- `proto/reportes.proto`  
